"""
linefinder.py
===========================
Module for the line finding.
"""

import warnings
from configparser import ConfigParser
from os import path
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
from scipy import interpolate

from gaiaxpy.calibrator.calibrator import calibrate
from gaiaxpy.config.paths import config_path
from gaiaxpy.converter.config import load_config, get_config
from gaiaxpy.converter.converter import convert
from gaiaxpy.core.dispersion_function import pwl_to_wl, pwl_range
from gaiaxpy.core.generic_functions import cast_output
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.linefinder.herm import HermiteDerivative
from gaiaxpy.linefinder.lines import Extrema, Lines
from gaiaxpy.linefinder.plotter import plot_spectra_with_lines
from gaiaxpy.output.line_data import LineData

warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))
config_file = path.join(config_path, config_parser.get('converter', 'optimised_bases'))

basis_function_id = {BANDS.bp: 56, BANDS.rp: 57}

tolerance = 1.  # [pix] tolerance to detect a line


def _get_configuration(config):
    """
    Get info from config file.
    
    Args:
        config (DataFrame): The configuration of the set of bases
                loaded into a DataFrame.
    
    Returns:
        (tuple): bases_transformation, n_bases, scale, offset
    """
    transformed_set_dimension = int(config['transformedSetDimension'].iloc[0])
    dimension = int(config['dimension'].iloc[0])
    if transformed_set_dimension == dimension:
        scale = (config['normalizedRange'].iloc(0)[0][1] - config['normalizedRange'].iloc(0)[0][0]) / \
                (config['range'].iloc(0)[0][1] - config['range'].iloc(0)[0][0])
        offset = config['normalizedRange'].iloc(0)[0][0] - config['range'].iloc(0)[0][0] * scale
        bases_transformation = config['transformationMatrix'].iloc(0)[0].reshape(dimension, transformed_set_dimension)
        return bases_transformation, dimension, scale, offset
    else:
        raise Exception('Transformation matrix is not square.')


def _x_to_pwl(x, scale, offset):
    return (x - offset) / scale


def _check_source_redshift_type(source_type, redshift):
    if not isinstance(source_type, str):
        raise ValueError('The variable source_type must be a string.')
    source_type = source_type.lower()
    if source_type not in ['qso', 'star']:
        raise ValueError("Unknown source type. Available source types: 'qso' and 'star'.")
    if source_type == 'qso' and not isinstance(redshift, list):
        raise ValueError('For QSOs please provide a list of redshifts.')
    return source_type


def _check_truncation(truncation):
    if not isinstance(truncation, bool):
        raise ValueError("Argument 'truncation' must contain a boolean value.")


def _check_plot_arguments(plot_spectra, save_plots):
    if not (isinstance(plot_spectra, bool) and isinstance(save_plots, bool)):
        raise ValueError("Arguments 'plot_spectra' and 'save_plots' must contain a boolean value.")
    if save_plots and not plot_spectra:
        raise ValueError("Argument 'plot_spectra' has to be set True if 'save_plots' is True.")


def _flux_interp(wl, flux):
    return interpolate.interp1d(wl, flux, fill_value='extrapolate')


def _get_line_pwl_width_test(roots_pwl2, line_root, xp):
    line_width_pwl = roots_pwl2[roots_pwl2 > line_root][0] - roots_pwl2[roots_pwl2 < line_root][-1]
    line_width = abs(pwl_to_wl(xp, roots_pwl2[roots_pwl2 > line_root][0]).item() -
                     pwl_to_wl(xp, roots_pwl2[roots_pwl2 < line_root][-1]).item())
    line_test = np.array([line_root - 2. * line_width_pwl, line_root - line_width_pwl,
                          line_root + line_width_pwl, line_root + 2. * line_width_pwl])

    return line_width_pwl, line_width, line_test


def _extract_elements_from_item(item, truncation, bp_n, rp_n):
    sid = item['source_id']
    # Coefficients from parsed_input_data
    bp_coeff, rp_coeff = item['bp_coefficients'], item['rp_coefficients']

    bp_rel_n = item['bp_n_relevant_bases'] if truncation else bp_n
    rp_rel_n = item['rp_n_relevant_bases'] if truncation else rp_n

    return sid, bp_coeff, rp_coeff, bp_rel_n, rp_rel_n


def _find(bases_transform_matrix, n_bases, n_rel_bases, scale, offset, xp, coeff, lines, line_names, calibrated_flux,
          calibrated_flux_err, flux, flux_err):
    """
    Line detection: get Hermite coefficients and try to detect lines from the list.
     
    Args:
        bases_transform_matrix (ndarray): Bases transformation matrix.
        n_bases (int): Number of bases.
        n_rel_bases (int): Number of relevant bases.
        scale (float): Scale.
        offset (float): Offset.
        xp (str): BP or RP.
        coeff (ndarray): Hermite coefficients.
        lines (list of floats): List of lines to detected [in pwl].
        line_names (list of str): List of line names.
        calibrated_flux (ndarray): Calibrated flux [W/nm/m2].
        calibrated_flux_err (ndarray): Error of calibrated flux.
        flux (ndarray): Flux in pwl [e/s].
        flux_err (ndarray): Error of flux.
    Returns:
        (list): Found lines with their properties.
    """
    h_der = HermiteDerivative(bases_transform_matrix, n_bases, n_rel_bases, coeff)
    roots_pwl = _x_to_pwl(h_der.get_roots_first_der(), scale, offset)
    roots_pwl2 = _x_to_pwl(h_der.get_roots_second_der(), scale, offset)

    found_lines = []
    for line_pwl, name in zip(lines, line_names):
        i_line = np.abs(roots_pwl - line_pwl).argmin()
        line_root = roots_pwl[i_line]
        if abs(line_pwl - line_root) < tolerance:  # Allow for difference in pwl
            line_width_pwl, line_width, line_test = _get_line_pwl_width_test(roots_pwl2, line_root, xp)
            line_continuum = np.median(calibrated_flux(pwl_to_wl(xp, line_test)))
            line_continuum_pwl = np.median(flux(line_test))

            line_wl = pwl_to_wl(xp, line_root).item()
            line_flux = calibrated_flux(line_wl).item()
            line_depth = line_flux - line_continuum
            line_depth_pwl = flux(line_root).item() - line_continuum_pwl
            line_sig = abs(line_depth) / calibrated_flux_err(line_wl)
            line_sig_pwl = abs(line_depth_pwl) / flux_err(line_root)
            found_lines.append((name, line_pwl, i_line, line_root, line_wl, line_flux, line_depth, line_width, line_sig,
                                line_continuum, line_sig_pwl, line_continuum_pwl, line_width_pwl))

    return found_lines


def _find_all(transform_matrix, n_bases, n_rel_bases, scale, offset, xp, coeff, calibrated_flux, calibrated_flux_err,
              flux, flux_err):
    """
    Extrema detection: get Hermite coefficients and try to detect all lines/extrema.
     
    Args:
        transform_matrix (ndarray): Bases transformation matrix.
        n_bases (int): Number of bases.
        n_rel_bases (int): Number of relevant bases.
        scale (float): Scale.
        offset (float): Offset.
        xp (str): BP or RP.
        coeff (ndarray): Hermite coefficients.
        calibrated_flux (ndarray): Calibrated flux.
        calibrated_flux_err (ndarray): Error of calibrated flux.
        flux (ndarray): Flux in pwl [e/s].
        flux_err (ndarray): Error of flux.
    Returns:
        (list): All found extrema (within dispersion function range) with their properties.
    """

    h_der = HermiteDerivative(transform_matrix, n_bases, n_rel_bases, coeff)

    roots_pwl = _x_to_pwl(h_der.get_roots_first_der(), scale, offset)
    roots_pwl2 = _x_to_pwl(h_der.get_roots_second_der(), scale, offset)

    _range = pwl_range(xp)
    mask = (roots_pwl > min(_range)) & (roots_pwl < max(_range))
    roots_pwl = roots_pwl[mask]

    found_lines = []

    for i_line, line_root in enumerate(roots_pwl):
        line_flux = calibrated_flux(pwl_to_wl(xp, line_root).item())
        line_width_pwl, line_width, line_test = _get_line_pwl_width_test(roots_pwl2, line_root, xp)
        line_continuum = np.median(calibrated_flux(pwl_to_wl(xp, line_test)))
        line_continuum_pwl = np.median(flux(line_test))
        line_depth = line_flux - line_continuum
        line_wl = pwl_to_wl(xp, line_root).item()
        line_sig = abs(line_depth) / calibrated_flux_err(line_wl)
        line_flux_pwl = flux(line_root).item()
        line_depth_pwl = line_flux_pwl - line_continuum_pwl
        line_sig_pwl = abs(line_depth_pwl) / flux_err(line_root)
        name = xp + '_' + str(int(line_wl))
        found_lines.append((name, line_root, i_line, line_root, line_wl, line_flux, line_depth, line_width, line_sig,
                            line_continuum, line_sig_pwl, line_continuum_pwl, line_width_pwl))
    return found_lines


def _find_fast(bases_transform_matrix, n_bases, n_rel_bases, scale, offset, xp, coeff):
    """
    Extrema (fast) detection: get Hermite coefficients and try to detect all lines/extrema.
     
    Args:
        bases_transform_matrix (ndarray): Bases transformation matrix.
        n_bases (int): Number of bases.
        n_rel_bases (int): Number of relevant bases.
        scale (float): Scale.
        offset (float): Offset.
        xp (str): BP or RP.
        coeff (ndarray): Hermite coefficients.
    Returns:
        (list): All found extrema (within dispersion function range).
    """
    h_der = HermiteDerivative(bases_transform_matrix, n_bases, n_rel_bases, coeff)
    roots_pwl = _x_to_pwl(h_der.get_roots_first_der(), scale, offset)
    _range = pwl_range(xp)
    mask = (roots_pwl > min(_range)) & (roots_pwl < max(_range))
    return roots_pwl[mask]


def _format_output(source_id, bp_found_lines, rp_found_lines):
    """
    Format output.
    """
    # source_id,line_name,wavelength_nm,line_flux,depth,width,significance,sig_pwl
    _bp_found_lines = [(source_id, line[0], line[4], line[5], line[6], line[7], line[8], line[10]) for line in
                       bp_found_lines]
    _rp_found_lines = [(source_id, line[0], line[4], line[5], line[6], line[7], line[8], line[10]) for line in
                       rp_found_lines]
    found_lines = _bp_found_lines + _rp_found_lines
    return sorted(found_lines, key=lambda x: x[2])


def linefinder(input_object: Union[list, Path, str], truncation: bool = False, source_type: str = 'star',
               redshift: Union[float, list] = None, user_lines: list = None, output_path: Union[Path, str] = '.',
               output_file: str = 'output_lines', output_format: str = None, save_file: bool = True,
               plot_spectra: bool = False, save_plots: bool = False, username: str = None, password: str = None):
    """
    Line finding: get the input internally calibrated mean spectra from the continuous representation to a
    sampled form. In between it looks for emission and absorption lines. The lines can be defined by user
    or chosen from internal library, the source redshift and type can be specified.
    
    Args:
        input_object (object): Path to the file containing the mean spectra as downloaded from the archive in their
            continuous representation, a list of sources ids (string or long), or a pandas DataFrame.
        truncation (bool): Toggle truncation of the set of bases. The level of truncation to be applied is defined by
            the recommended value in the input files.
        source_type (str): Source type: 'star' or 'qso'.
        redshift (list): List containing tuples of pairs (source id - redshift) for QSOs
        user_lines (list): List containing tuples of wavelengths [nm] and names (e.g. [(65.64, 48.62),
            ('Line1', 'Line2')]).
        output_path (Path/str): Path where to save the output data.
        output_file (str): Name of the output file without extension (e.g. 'my_file').
        output_format (str): Desired output format. If no format is given, the output file format will be the same as
            the input file (e.g. 'csv').
        save_file (bool): Whether to save the output in a file. If false, output_format and output_file will be ignored.
        plot_spectra (bool): Whether to plot spectrum with lines.
        save_plots (bool): Whether to save plots with spectra.
        username (str): Cosmos username, only suggested when input_object is a list or ADQL query.
        password (str): Cosmos password, only suggested when input_object is a list or ADQL query.
        
    Returns:
        (DataFrame): dataframe with arrays of found lines and their properties for each source
    """
    source_type = _check_source_redshift_type(source_type, redshift)
    _check_truncation(truncation)

    config_df = load_config(config_file)
    bp_tm, bp_n, bp_scale, bp_offset = _get_configuration(get_config(config_df, basis_function_id[BANDS.bp]))
    rp_tm, rp_n, rp_scale, rp_offset = _get_configuration(get_config(config_df, basis_function_id[BANDS.rp]))

    # Parse input
    parsed_input_data, extension = InputReader(input_object, linefinder, username, password).read()

    # Get converted spectra
    con_spectra, con_sampling = convert(parsed_input_data, truncation=truncation, save_file=False)
    # Get calibrated spectra
    cal_spectra, cal_sampling = calibrate(parsed_input_data, truncation=truncation, save_file=False)
    # Get calibrated continuum (limit number of bases) -> TO DO: rethink this approach
    temp_input_data = parsed_input_data.copy(deep=True)
    temp_input_data['bp_n_relevant_bases'], temp_input_data['rp_n_relevant_bases'] = 3, 3
    cal_continuum, _ = calibrate(temp_input_data, truncation=True, save_file=False)
    # Get source_ids
    source_ids = parsed_input_data['source_id']

    # Prep redshifts -> match with source_ids
    if source_type == 'qso':
        red_array = np.array(redshift, dtype=[('source_id', 'i8'), ('z', 'f8')])
        if not np.all(np.isin(source_ids, red_array['source_id'])):
            raise ValueError('Missing redshifts in the list?')

    # Prep lines
    bp_lines = Lines(BANDS.bp, source_type, user_lines=user_lines)
    rp_lines = Lines(BANDS.rp, source_type, user_lines=user_lines)

    if source_type == 'star':
        bp_line_names, bp_lines_pwl = bp_lines.get_lines_pwl()
        rp_line_names, rp_lines_pwl = rp_lines.get_lines_pwl()

    output_lines = []

    for i in np.arange(len(parsed_input_data)):
        _item = parsed_input_data.iloc[i]
        sid, bp_coeff, rp_coeff, bp_rel_n, rp_rel_n = _extract_elements_from_item(_item, truncation, bp_n, rp_n)

        # Prep lines cont.
        if source_type == 'qso':
            bp_line_names, bp_lines_pwl = bp_lines.get_lines_pwl(zet=red_array['z'][red_array['source_id'] == sid][0])
            rp_line_names, rp_lines_pwl = rp_lines.get_lines_pwl(zet=red_array['z'][red_array['source_id'] == sid][0])

        # Masks
        m_cal = (cal_spectra['source_id'] == sid)
        m_con_bp = (con_spectra['source_id'] == sid) & (con_spectra['xp'] == 'BP')
        m_con_rp = (con_spectra['source_id'] == sid) & (con_spectra['xp'] == 'RP')

        # Run line finder for BP
        if not pd.isna(_item['bp_n_parameters']):
            bp_found_lines = _find(bp_tm, bp_n, bp_rel_n, bp_scale, bp_offset, BANDS.bp, bp_coeff, bp_lines_pwl,
                                   bp_line_names, _flux_interp(cal_sampling, cal_spectra[m_cal]['flux'].values[0]),
                                   _flux_interp(cal_sampling, cal_spectra[m_cal]['flux_error'].values[0]),
                                   _flux_interp(con_sampling, con_spectra[m_con_bp]['flux'].values[0]),
                                   _flux_interp(con_sampling, con_spectra[m_con_bp]['flux_error'].values[0]))
        else:
            bp_found_lines = []

        # Run line finder for RP
        rp_found_lines = _find(rp_tm, rp_n, rp_rel_n, rp_scale, rp_offset, BANDS.rp, rp_coeff, rp_lines_pwl,
                               rp_line_names, _flux_interp(cal_sampling, cal_spectra[m_cal]['flux'].values[0]),
                               _flux_interp(cal_sampling, cal_spectra[m_cal]['flux_error'].values[0]),
                               _flux_interp(con_sampling, con_spectra[m_con_rp]['flux'].values[0]),
                               _flux_interp(con_sampling, con_spectra[m_con_rp]['flux_error'].values[0]))

        # Plotting
        if plot_spectra and not pd.isna(_item['bp_n_parameters']):
            plot_spectra_with_lines(sid, con_sampling, con_spectra[m_con_bp]['flux'].values[0],
                                    con_spectra[m_con_rp]['flux'].values[0], cal_sampling,
                                    cal_spectra[m_cal]['flux'].values[0], bp_found_lines, rp_found_lines, save_plots)
        elif plot_spectra:
            plot_spectra_with_lines(sid, con_sampling, None, con_spectra[m_con_rp]['flux'].values[0], cal_sampling,
                                    cal_spectra[m_cal]['flux'].values[0], bp_found_lines, rp_found_lines, save_plots)

        output_lines.extend(_format_output(sid, bp_found_lines, rp_found_lines))

    output_df = pd.DataFrame(output_lines, columns=['source_id', 'line_name', 'wavelength_nm', 'line_flux', 'depth',
                                                    'width', 'significance', 'sig_pwl'])
    output_data = LineData(output_df)
    output_data.data = cast_output(output_data)
    output_data.data.attrs['data_type'] = Lines('xp', source_type)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return output_data.data


def extremafinder(input_object: Union[list, Path, str], truncation: bool = False, output_path: Union[Path, str] = '.',
                  output_file: str = 'output_lines', output_format: str = None, save_file: bool = True,
                  plot_spectra: bool = False, save_plots: bool = False, username=None, password=None) -> pd.DataFrame:
    """
    Line finding: get the input internally calibrated mean spectra from the continuous representation to a
    sampled form. In between it looks for all lines (=extrema in spectra).
    
    Args:
        input_object (object): Path to the file containing the mean spectra as downloaded from the archive in their
            continuous representation, a list of sources ids (string or long), or a pandas DataFrame.
        truncation (bool): Toggle truncation of the set of bases. The level of truncation to be applied is defined by
            the recommended value in the input files.
        output_path (Path/str): Path where to save the output data.
        output_file (str): Name of the output file without extension (e.g. 'my_file').
        output_format (str): Desired output format. If no format is given, the output file format will be the same as
            the input file (e.g. 'csv').
        save_file (bool): Whether to save the output in a file. If false, output_format and output_file will be ignored.
        plot_spectra (bool): Whether to plot spectrum with lines.
        save_plots (bool): Whether to save plots with spectra.
        username (str): Cosmos username, only suggested when input_object is a list or ADQL query.
        password (str): Cosmos password, only suggested when input_object is a list or ADQL query.
        
    Returns:
        (DataFrame): dataframe with values of found extrema.
    """
    _check_truncation(truncation)
    _check_plot_arguments(plot_spectra, save_plots)

    config_df = load_config(config_file)
    bp_tm, bp_n, bp_scale, bp_offset = _get_configuration(get_config(config_df, basis_function_id[BANDS.bp]))
    rp_tm, rp_n, rp_scale, rp_offset = _get_configuration(get_config(config_df, basis_function_id[BANDS.rp]))

    # Parse input
    parsed_input_data, extension = InputReader(input_object, linefinder, username, password).read()

    # Get converted spectra
    con_spectra, con_sampling = convert(parsed_input_data, truncation=truncation, save_file=False)
    # Get calibrated spectra
    cal_spectra, cal_sampling = calibrate(parsed_input_data, truncation=truncation, save_file=False)
    # Get calibrated continuum (limit number of bases)
    temp_input_data = parsed_input_data.copy(deep=True)
    temp_input_data['bp_n_relevant_bases'], temp_input_data['rp_n_relevant_bases'] = 3, 3
    cal_continuum, _ = calibrate(temp_input_data, truncation=True, save_file=False)

    output_lines = []
    for i in np.arange(len(parsed_input_data)):
        item = parsed_input_data.iloc[i]
        sid, bp_coeff, rp_coeff, bp_rel_n, rp_rel_n = _extract_elements_from_item(item, truncation, bp_n, rp_n)
        # Masks
        m_cal = (cal_spectra['source_id'] == sid)
        m_con_bp = (con_spectra['source_id'] == sid) & (con_spectra['xp'] == 'BP')
        m_con_rp = (con_spectra['source_id'] == sid) & (con_spectra['xp'] == 'RP')

        # Run line finder for BP
        if pd.isna(item['bp_n_parameters']):
            bp_found_lines = []
        else:
            bp_found_lines = _find_all(bp_tm, bp_n, bp_rel_n, bp_scale, bp_offset, BANDS.bp, bp_coeff,
                                       _flux_interp(cal_sampling, cal_spectra[m_cal]['flux'].values[0]),
                                       _flux_interp(cal_sampling, cal_spectra[m_cal]['flux_error'].values[0]),
                                       _flux_interp(con_sampling, con_spectra[m_con_bp]['flux'].values[0]),
                                       _flux_interp(con_sampling, con_spectra[m_con_bp]['flux_error'].values[0]))

        # Run line finder for RP
        rp_found_lines = _find_all(rp_tm, rp_n, rp_rel_n, rp_scale, rp_offset, BANDS.rp, rp_coeff,
                                   _flux_interp(cal_sampling, cal_spectra[m_cal]['flux'].values[0]),
                                   _flux_interp(cal_sampling, cal_spectra[m_cal]['flux_error'].values[0]),
                                   _flux_interp(con_sampling, con_spectra[m_con_rp]['flux'].values[0]),
                                   _flux_interp(con_sampling, con_spectra[m_con_rp]['flux_error'].values[0]))

        # Plotting
        if plot_spectra and not pd.isna(item['bp_n_parameters']):
            plot_spectra_with_lines(sid, con_sampling, con_spectra[m_con_bp]['flux'].values[0],
                                    con_spectra[m_con_rp]['flux'].values[0], cal_sampling,
                                    cal_spectra[m_cal]['flux'].values[0], bp_found_lines, rp_found_lines, save_plots)
        elif plot_spectra:
            plot_spectra_with_lines(sid, con_sampling, None, con_spectra[m_con_rp]['flux'].values[0], cal_sampling,
                                    cal_spectra[m_cal]['flux'].values[0], bp_found_lines, rp_found_lines, save_plots)

        output_lines.extend(_format_output(sid, bp_found_lines, rp_found_lines))

    output_df = pd.DataFrame(output_lines, columns=['source_id', 'line_name', 'wavelength_nm', 'line_flux', 'depth',
                                                    'width', 'significance', 'sig_pwl'])
    output_data = LineData(output_df)
    output_data.data = cast_output(output_data)
    output_data.data.attrs['data_type'] = Lines('xp', 'star')
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return output_data.data


def fastfinder(input_object: Union[list, Path, str], truncation: bool = False, output_path: Union[Path, str] = '.',
               output_file: str = 'output_lines', output_format: str = None, save_file: bool = True, username=None,
               password=None) -> pd.DataFrame:
    """
    Line finding: get the input coefficients for internally calibrated mean spectra and look for the extrema.
    No evaluation of spectra in both sampled and continuous forms is performed.
    
    Args:
        input_object (object): Path to the file containing the mean spectra as downloaded from the archive in their
            continuous representation, a list of sources ids (string or long), or a pandas DataFrame.
        truncation (bool): Toggle truncation of the set of bases. The level of truncation to be applied is defined by
            the recommended value in the input files.
        output_path (Path/str): Path where to save the output data.
        output_file (str): Name of the output file without extension (e.g. 'my_file').
        output_format (str): Desired output format. If no format is given, the output file format will be the same as
            the input file (e.g. 'csv').
        save_file (bool): Whether to save the output in a file. If false, output_format and output_file will be ignored.
        username (str): Cosmos username, only suggested when input_object is a list or ADQL query.
        password (str): Cosmos password, only suggested when input_object is a list or ADQL query.
        
    Returns:
        (DataFrame): dataframe with arrays of found extrema for each source
    """
    _check_truncation(truncation)

    config_df = load_config(config_file)
    bp_tm, bp_n, bp_scale, bp_offset = _get_configuration(get_config(config_df, basis_function_id[BANDS.bp]))
    rp_tm, rp_n, rp_scale, rp_offset = _get_configuration(get_config(config_df, basis_function_id[BANDS.rp]))

    parsed_input_data, extension = InputReader(input_object, linefinder, username, password).read()

    output_rows = []
    for i in np.arange(len(parsed_input_data)):
        item = parsed_input_data.iloc[i]
        sid, bp_coeff, rp_coeff, bp_rel_n, rp_rel_n = _extract_elements_from_item(item, truncation, bp_n, rp_n)

        # Run line finder for BP
        bp_found_lines = [] if pd.isna(item['bp_n_parameters']) else _find_fast(bp_tm, bp_n, bp_rel_n, bp_scale,
                                                                                bp_offset, BANDS.bp, bp_coeff)

        # Run line finder for RP (there are no sources with missing RP, but this could help spot errors)
        rp_found_lines = [] if pd.isna(item['rp_n_parameters']) else _find_fast(rp_tm, rp_n, rp_rel_n, rp_scale,
                                                                                rp_offset, BANDS.rp, rp_coeff)

        output_bp_rows = [[sid, BANDS.bp.upper(), value] for value in bp_found_lines]
        output_rp_rows = [[sid, BANDS.rp.upper(), value] for value in rp_found_lines]
        output_i_rows = output_bp_rows + output_rp_rows
        output_rows.extend(output_i_rows)

    output_df = pd.DataFrame(output_rows, columns=['source_id', 'xp', 'extrema'])
    output_data = LineData(output_df)
    output_data.data = cast_output(output_data)
    output_data.data.attrs['data_type'] = Extrema()
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return output_data.data
