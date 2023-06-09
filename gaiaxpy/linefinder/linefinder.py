"""
linefinder.py
===========================
Module for the line finding.
"""

import warnings
from configparser import ConfigParser
from os import path
from pathlib import Path
from tqdm import tqdm
from typing import Union

import numpy as np
import pandas as pd
from scipy import interpolate

from gaiaxpy.calibrator.calibrator import _calibrate
from gaiaxpy.config.paths import config_path
from gaiaxpy.converter.config import load_config, get_config
from gaiaxpy.converter.converter import _convert
from gaiaxpy.core.dispersion_function import pwl_to_wl, pwl_range
from gaiaxpy.core.generic_functions import cast_output
from gaiaxpy.core.generic_variables import pbar_units, pbar_colour, pbar_message
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.linefinder.herm import HermiteDerivative
from gaiaxpy.linefinder.lines import Extrema, Lines
from gaiaxpy.linefinder.plotter import plot_spectra_with_lines
from gaiaxpy.output.line_data import LineData

warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)

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


def _get_configuration_variables(_config_file, _basis_function_id):
    config_df = load_config(_config_file)
    bp_tm, bp_n, bp_scale, bp_offset = _get_configuration(get_config(config_df, _basis_function_id[BANDS.bp]))
    rp_tm, rp_n, rp_scale, rp_offset = _get_configuration(get_config(config_df, _basis_function_id[BANDS.rp]))
    return bp_tm, bp_n, bp_scale, bp_offset, rp_tm, rp_n, rp_scale, rp_offset


def _get_masks(cal_spectra, con_spectra, sid):
    m_cal = (cal_spectra.index == sid)
    m_con_bp = (con_spectra.index == sid) & (con_spectra['xp'] == 'BP')
    m_con_rp = (con_spectra.index == sid) & (con_spectra['xp'] == 'RP')
    return m_cal, m_con_bp, m_con_rp


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


def _get_line_pwl_width_test_arrays(roots_pwl2, line_roots, xp):
    line_width_pwl_values = np.empty_like(line_roots)
    line_widths = np.empty_like(line_roots)
    for i, line_root in enumerate(line_roots):
        mask_greater = roots_pwl2 > line_roots[:, np.newaxis]
        mask_less = roots_pwl2 < line_roots[:, np.newaxis]
        line_width_pwl_values[i] = roots_pwl2[mask_greater[i]][0] - roots_pwl2[mask_less[i]][-1]
        line_widths[i] = np.abs(pwl_to_wl(xp, roots_pwl2[mask_greater[i]][0]) -
                                pwl_to_wl(xp, roots_pwl2[mask_less[i]][-1]))
    line_tests = np.column_stack((line_roots - 2. * line_width_pwl_values, line_roots - line_width_pwl_values,
                                  line_roots + line_width_pwl_values, line_roots + 2. * line_width_pwl_values))
    return line_width_pwl_values, line_widths, line_tests


def _extract_elements_from_item(item, truncation, bp_n, rp_n):
    bp_rel_n = item['bp_n_relevant_bases'] if truncation else bp_n
    rp_rel_n = item['rp_n_relevant_bases'] if truncation else rp_n
    return item['source_id'], item['bp_coefficients'], item['rp_coefficients'], bp_rel_n, rp_rel_n


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

    lines = np.array(lines)
    i_lines = np.argmin(np.abs(roots_pwl[:, None] - lines), axis=0)
    line_roots = roots_pwl[i_lines]
    mask = np.abs(lines - line_roots) < tolerance

    line_names = line_names[mask]
    lines = lines[mask]
    line_roots = line_roots[mask]
    i_lines = i_lines[mask]

    if len(lines) != len(line_names) or len(line_names) != len(line_roots):
        raise ValueError("The length of the inputs don't match. Check the values for lines.")

    if lines.size == 0:
        return []

    line_width_pwl_values, line_widths, line_tests = _get_line_pwl_width_test_arrays(roots_pwl2, line_roots, xp)
    line_continuum_values = np.median(calibrated_flux(pwl_to_wl(xp, line_tests)), axis=1)
    line_continuum_pwl_values = np.median(flux(line_tests), axis=1)
    line_wl_values = pwl_to_wl(xp, line_roots).flatten()
    line_flux_values = calibrated_flux(line_wl_values).flatten()
    line_depth_values = line_flux_values - line_continuum_values
    line_depth_pwl_values = flux(line_roots) - line_continuum_pwl_values
    line_sig_values = np.abs(line_depth_values) / calibrated_flux_err(line_wl_values)
    line_sig_pwl_values = abs(line_depth_pwl_values) / flux_err(line_roots)
    return [(name, line_pwl, i_line, line_root, line_wl, line_flux, line_depth, line_width, line_sig, line_continuum,
             line_sig_pwl, line_continuum_pwl, line_width_pwl) for name, line_pwl, line_root, i_line, line_width_pwl,
             line_width, line_test, line_continuum, line_continuum_pwl, line_wl, line_flux, line_depth, line_depth_pwl,
             line_sig, line_sig_pwl in zip(line_names, lines, line_roots, i_lines, line_width_pwl_values, line_widths,
                                           line_tests, line_continuum_values, line_continuum_pwl_values, line_wl_values,
                                           line_flux_values, line_depth_values, line_depth_pwl_values, line_sig_values,
                                           line_sig_pwl_values)]


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

    line_width_pwl_values, line_widths, line_tests = _get_line_pwl_width_test_arrays(roots_pwl2, roots_pwl, xp)
    line_flux_values = calibrated_flux(pwl_to_wl(xp, roots_pwl)).flatten()
    line_continuum_values = np.median(calibrated_flux(pwl_to_wl(xp, line_tests)), axis=1)
    line_continuum_pwl_values = np.median(flux(line_tests), axis=1)
    line_depth_values = line_flux_values - line_continuum_values
    line_wl_values = pwl_to_wl(xp, roots_pwl).flatten()
    line_sig_values = np.abs(line_depth_values) / calibrated_flux_err(line_wl_values)
    line_flux_pwl_values = flux(roots_pwl).flatten()
    line_depth_pwl_values = line_flux_pwl_values - line_continuum_pwl_values
    line_sig_pwl_values = np.abs(line_depth_pwl_values) / flux_err(roots_pwl)
    line_names = [xp + '_' + str(int(line_wl)) for line_wl in line_wl_values]

    return [(name, line_root, i_line, line_root, line_wl, line_flux, line_depth, line_width, line_sig, line_continuum,
             line_sig_pwl, line_continuum_pwl, line_width_pwl) \
            for i_line, (line_root, line_width_pwl, line_width, line_test, line_flux, line_continuum, line_continuum_pwl,
                         line_depth, line_wl, line_sig, line_flux_pwl, line_depth_pwl, line_sig_pwl, name) \
            in enumerate(zip(roots_pwl, line_width_pwl_values, line_widths, line_tests, line_flux_values,
                             line_continuum_values, line_continuum_pwl_values, line_depth_values, line_wl_values,
                             line_sig_values, line_flux_pwl_values, line_depth_pwl_values, line_sig_pwl_values,
                             line_names))]


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
    Format output. Finder functions generate more rows than they're required for the output. These rows are generated
    so that the output can be plotted. Ideally, when plot_spectra is set to False, the extra rows shouldn't be computed.
    """
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
    __FUNCTION_KEY = 'linefinder'
    source_type = _check_source_redshift_type(source_type, redshift)
    _check_truncation(truncation)

    bp_tm, bp_n, bp_scale, bp_offset, rp_tm, rp_n, rp_scale, rp_offset = _get_configuration_variables(config_file,
                                                                                                      basis_function_id)
    # Parse input
    parsed_input_data, extension = InputReader(input_object, linefinder, username, password).read()
    # Internal info will be disabled, but the user will need some info
    print('Preparing required internal data...' + ' '* 10, end='\r')
    # Get converted spectra
    con_spectra, con_sampling = _convert(parsed_input_data, truncation=truncation, save_file=False, disable_info=True)
    # Get calibrated spectra
    cal_spectra, cal_sampling = _calibrate(parsed_input_data, truncation=truncation, save_file=False, disable_info=True)
    # Set indices as we'll need to search for values in the frames many times
    cal_spectra = cal_spectra.set_index('source_id')
    con_spectra = con_spectra.set_index('source_id')
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
    parsed_input_data_dict = parsed_input_data.to_dict('records')
    for row in tqdm(parsed_input_data_dict, desc=pbar_message[__FUNCTION_KEY],
                    unit=pbar_units[__FUNCTION_KEY], leave=False, colour=pbar_colour):
        sid, bp_coeff, rp_coeff, bp_rel_n, rp_rel_n = _extract_elements_from_item(row, truncation, bp_n, rp_n)

        # Prep lines cont.
        if source_type == 'qso':
            bp_line_names, bp_lines_pwl = bp_lines.get_lines_pwl(zet=red_array['z'][red_array['source_id'] == sid][0])
            rp_line_names, rp_lines_pwl = rp_lines.get_lines_pwl(zet=red_array['z'][red_array['source_id'] == sid][0])

        # Masks
        m_cal, m_con_bp, m_con_rp = _get_masks(cal_spectra, con_spectra, sid)

        is_na_bp_np = pd.isna(row['bp_n_parameters'])
        is_na_rp_np = pd.isna(row['rp_n_parameters'])

        _cal_spectra_m_cal_flux = cal_spectra[m_cal]['flux'].values[0]
        _interp_m_cal_flux = _flux_interp(cal_sampling, _cal_spectra_m_cal_flux)
        _interp_m_cal_flux_error = _flux_interp(cal_sampling, cal_spectra[m_cal]['flux_error'].values[0])
        _con_spectra_m_con_rp_flux = con_spectra[m_con_rp]['flux'].values[0]

        # Run line finder for BP
        bp_found_lines = [] if is_na_bp_np else _find(
            bp_tm, bp_n, bp_rel_n, bp_scale, bp_offset, BANDS.bp, bp_coeff, bp_lines_pwl, bp_line_names,
            _interp_m_cal_flux, _interp_m_cal_flux_error,
            _flux_interp(con_sampling, con_spectra[m_con_bp]['flux'].values[0]),
            _flux_interp(con_sampling, con_spectra[m_con_bp]['flux_error'].values[0]))

        # Run line finder for RP
        rp_found_lines = [] if is_na_rp_np else _find(
            rp_tm, rp_n, rp_rel_n, rp_scale, rp_offset, BANDS.rp, rp_coeff, rp_lines_pwl, rp_line_names,
            _interp_m_cal_flux, _interp_m_cal_flux_error, _flux_interp(con_sampling, _con_spectra_m_con_rp_flux),
            _flux_interp(con_sampling, con_spectra[m_con_rp]['flux_error'].values[0]))

        # Plotting
        if plot_spectra:
            con_spectra_m_con_bp_flux_values = None if is_na_bp_np else con_spectra[m_con_bp]['flux'].values[0]
            plot_spectra_with_lines(sid, con_sampling, con_spectra_m_con_bp_flux_values, _con_spectra_m_con_rp_flux,
                                    cal_sampling, _cal_spectra_m_cal_flux, bp_found_lines, rp_found_lines, save_plots,
                                    output_path, prefix='lines')

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
    __FUNCTION_KEY = 'extremafinder'
    _check_truncation(truncation)
    _check_plot_arguments(plot_spectra, save_plots)

    bp_tm, bp_n, bp_scale, bp_offset, rp_tm, rp_n, rp_scale, rp_offset = _get_configuration_variables(config_file,
                                                                                                      basis_function_id)
    # Parse input
    parsed_input_data, extension = InputReader(input_object, linefinder, username, password).read()
    # Internal info will be disabled, but the user will need some info
    print('Preparing required internal data...' + ' '* 10, end='\r')
    # Get converted spectra
    con_spectra, con_sampling = _convert(parsed_input_data, truncation=truncation, save_file=False, disable_info=True)
    # Get calibrated spectra
    cal_spectra, cal_sampling = _calibrate(parsed_input_data, truncation=truncation, save_file=False, disable_info=True)
    # Set indices as we'll need to search for values in the frames many times
    cal_spectra = cal_spectra.set_index('source_id')
    con_spectra = con_spectra.set_index('source_id')

    output_lines = []
    parsed_input_data_dict = parsed_input_data.to_dict('records')
    for row in tqdm(parsed_input_data_dict, desc=pbar_message[__FUNCTION_KEY], unit=pbar_units[__FUNCTION_KEY],
                    leave=False, colour=pbar_colour):
        sid, bp_coeff, rp_coeff, bp_rel_n, rp_rel_n = _extract_elements_from_item(row, truncation, bp_n, rp_n)
        # Masks
        m_cal, m_con_bp, m_con_rp = _get_masks(cal_spectra, con_spectra, sid)

        is_na_bp_np = pd.isna(row['bp_n_parameters'])
        is_na_rp_np = pd.isna(row['rp_n_parameters'])

        _interp_m_cal_flux = _flux_interp(cal_sampling, cal_spectra[m_cal]['flux'].values[0])
        _interp_m_cal_flux_error = _flux_interp(cal_sampling, cal_spectra[m_cal]['flux_error'].values[0])
        _con_spectra_m_con_rp_flux = con_spectra[m_con_rp]['flux'].values[0]

        # Run line finder for BP
        bp_found_lines = [] if is_na_bp_np else _find_all(bp_tm, bp_n, bp_rel_n, bp_scale, bp_offset, BANDS.bp, bp_coeff,
                                                          _interp_m_cal_flux, _interp_m_cal_flux_error,
                                                          _flux_interp(con_sampling,
                                                                       con_spectra[m_con_bp]['flux'].values[0]),
                                                          _flux_interp(con_sampling,
                                                                       con_spectra[m_con_bp]['flux_error'].values[0]))
        # Run line finder for RP (is_na_rp_np is expected to be False always)
        rp_found_lines = [] if is_na_rp_np else _find_all(rp_tm, rp_n, rp_rel_n, rp_scale, rp_offset, BANDS.rp, rp_coeff,
                                                          _interp_m_cal_flux, _interp_m_cal_flux_error,
                                                          _flux_interp(con_sampling, _con_spectra_m_con_rp_flux),
                                                          _flux_interp(con_sampling,
                                                                       con_spectra[m_con_rp]['flux_error'].values[0]))
        # Plotting
        if plot_spectra:
            con_spectra_m_con_bp_flux_values = None if is_na_bp_np else con_spectra[m_con_bp]['flux'].values[0]
            plot_spectra_with_lines(sid, con_sampling, con_spectra_m_con_bp_flux_values,
                                    _con_spectra_m_con_rp_flux, cal_sampling,
                                    cal_spectra[m_cal]['flux'].values[0], bp_found_lines, rp_found_lines, save_plots,
                                    output_path, prefix='extrema')

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
    __FUNCTION_KEY = 'fastfinder'
    _check_truncation(truncation)
    bp_tm, bp_n, bp_scale, bp_offset, rp_tm, rp_n, rp_scale, rp_offset = _get_configuration_variables(config_file,
                                                                                                      basis_function_id)
    parsed_input_data, extension = InputReader(input_object, linefinder, username, password).read()
    parsed_input_data_dict = parsed_input_data.to_dict('records')

    def process_rows():
        for row in tqdm(parsed_input_data_dict, desc=pbar_message[__FUNCTION_KEY], unit=pbar_units[__FUNCTION_KEY],
                        leave=False, colour=pbar_colour):
            sid, bp_coeff, rp_coeff, bp_rel_n, rp_rel_n = _extract_elements_from_item(row, truncation, bp_n, rp_n)
            # Run line finder for BP
            bp_found_lines = [] if pd.isna(row['bp_n_parameters']) else _find_fast(bp_tm, bp_n, bp_rel_n, bp_scale,
                                                                                   bp_offset, BANDS.bp, bp_coeff)
            # Run line finder for RP (there are no sources with missing RP, but this could help spot errors)
            rp_found_lines = [] if pd.isna(row['rp_n_parameters']) else _find_fast(rp_tm, rp_n, rp_rel_n, rp_scale,
                                                                                   rp_offset, BANDS.rp, rp_coeff)
            output_bp_rows = ([sid, BANDS.bp.upper(), value] for value in bp_found_lines)
            output_rp_rows = ([sid, BANDS.rp.upper(), value] for value in rp_found_lines)
            yield from output_bp_rows
            yield from output_rp_rows

    output_rows = []
    output_rows.extend(process_rows())
    output_df = pd.DataFrame(output_rows, columns=['source_id', 'xp', 'extrema'])
    output_data = LineData(output_df)
    output_data.data = cast_output(output_data)
    output_data.data.attrs['data_type'] = Extrema()
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return output_data.data
