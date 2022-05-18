"""
calibrator.py
====================================
Module for the calibrator functionality.
"""

import numpy as np
import pandas as pd
from configparser import ConfigParser
from pathlib import Path
from os.path import join
from .external_instrument_model import ExternalInstrumentModel
from gaiaxpy.config import config_path
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.core import _get_spectra_type, _load_xpmerge_from_csv, \
                         _load_xpsampling_from_csv, _progress_tracker, \
                         _validate_arguments, _validate_wl_sampling, satellite
from gaiaxpy.input_reader import InputReader
from gaiaxpy.output import SampledSpectraData
from gaiaxpy.spectrum import _get_covariance_matrix, AbsoluteSampledSpectrum, \
                             SampledBasisFunctions, XpContinuousSpectrum

config_parser = ConfigParser()
config_parser.read(join(config_path, 'config.ini'))


def calibrate(
        input_object,
        sampling=None,
        truncation=False,
        output_path='.',
        output_file='output_spectra',
        output_format=None,
        save_file=True,
        username=None,
        password=None):
    """
    Calibration utility: calibrates the input internally-calibrated
    continuously-represented mean spectra to the absolute system. An absolute
    spectrum sampled on a user-defined or default wavelength grid is created
    for each set of BP and RP input spectra. If either band is missing, the
    output spectrum will only cover the range covered by the available data.

    Args:
        input_object (object): Path to the file containing the mean spectra
             as downloaded from the archive in their continuous representation,
             a list of sources ids (string or long), or a pandas DataFrame.
        sampling (ndarray): 1D array containing the desired sampling in
             absolute wavelengths [nm].
        truncation (bool): Toggle truncation of the set of bases. The level
             of truncation to be applied is defined by the recommended value in
             the input files.
        output_path (str): Path where to save the output data.
        output_file (str): Name of the output file.
        output_format (str): Format to be used for the output file. If no format
            is given, then the output file will be in the same format as the
            input file.
        save_file (bool): Whether to save the output in a file. If false, output_format
            and output_file are ignored.
        username (str): Cosmos username, only required when the input_object is a list or ADQL query.
        password (str): Cosmos password, only required when the input_object is a list or ADQL query.

    Returns:
        (tuple): tuple containing:

            DataFrame: The values for all sampled absolute spectra.
            ndarray: The sampling used to calibrate the input spectra (user-provided or default).
    """
    # Call internal method
    return _calibrate(
        input_object,
        sampling,
        truncation,
        output_path,
        output_file,
        output_format,
        save_file,
        username=username,
        password=password)


def _calibrate(
        input_object,
        sampling=None,
        truncation=False,
        output_path='.',
        output_file='output_spectra',
        output_format=None,
        save_file=True,
        bp_model='v375wi',
        rp_model='v142r',
        username=None,
        password=None):
    """
    Internal method of the calibration utility. Refer to "calibrate".

    Args:
        bp_model (str): BP model to use.
        rp_model (str): RP model to use.

    Returns:
        DataFrame: A list of all sampled absolute spectra.
        ndarray: The sampling used to calibrate the spectra.

    Raises:
        ValueError: If the sampling is out of the expected boundaries.
    """
    _validate_wl_sampling(sampling)
    _validate_arguments(_calibrate.__defaults__[3], output_file, save_file)
    parsed_input_data, extension = InputReader(input_object, _calibrate, username, password)._read()
    label = 'calibrator'

    xp_design_matrices, xp_merge = _generate_xp_matrices_and_merge(label, sampling, bp_model, rp_model)
    # Create sampled basis functions
    spectra_list = _create_spectra(parsed_input_data, truncation, xp_design_matrices, xp_merge)
    # Generate output
    spectra_df = pd.DataFrame.from_records([spectrum._spectrum_to_dict() for spectrum in spectra_list])
    spectra_type = _get_spectra_type(spectra_list)
    spectra_df.attrs['data_type'] = spectra_type
    positions = spectra_list[0]._get_positions()
    output_data = SampledSpectraData(spectra_df, positions)
    # Save output
    Path(output_path).mkdir(parents=True, exist_ok=True)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return spectra_df, positions


def _create_merge(xp, sampling):
    """
    Create the weight information on the input sampling grid.

    Args:
        xp (str): Band (either BP or RP).
        sampling (ndarray): 1D array containing the sampling grid.

    Returns:
        dict: A dictionary containing a BP and an RP array with weights.
    """
    wl_high = satellite.BP_WL.high
    wl_low = satellite.RP_WL.low

    if xp == BANDS.bp:
        weight = np.array([1.0 if wl < wl_low else 0.0 if wl > wl_high else (
            1.0 - (wl - wl_low) / (wl_high - wl_low)) for wl in sampling])
    elif xp == BANDS.rp:
        weight = np.array([0.0 if wl < wl_low else 1.0 if wl > wl_high else (
            wl - wl_low) / (wl_high - wl_low) for wl in sampling])
    else:
        raise ValueError(f'Given band is {xp}, but should be either bp or rp.')
    return weight


def _generate_xp_matrices_and_merge(label, sampling, bp_model, rp_model):
    """
    Get xp_design_matrices and xp_merge.
    """
    def _get_file_for_xp(xp, key, bp_model=bp_model, rp_model=rp_model):
        file_name = config_parser.get(label, key)
        if xp == BANDS.bp:
            model = bp_model
        elif xp == BANDS.rp:
            model = rp_model
        return join(config_path, f"{file_name.replace('xp', xp).replace('model', model)}".format(key))

    xp_design_matrices = {}
    if sampling is None:
        xp_sampling_grid, xp_merge = _load_xpmerge_from_csv(label, bp_model=bp_model)
        xp_design_matrices = _load_xpsampling_from_csv(label, bp_model=bp_model)
        for xp in BANDS:
            xp_design_matrices[xp] = SampledBasisFunctions.from_design_matrix(
                xp_sampling_grid, xp_design_matrices[xp])
    else:
        xp_merge = {}
        for xp in BANDS:
            instr_model = ExternalInstrumentModel.from_config_csv(
                _get_file_for_xp(
                    xp, 'dispersion'), _get_file_for_xp(
                    xp, 'response'), _get_file_for_xp(
                    xp, 'bases'))
            xp_merge[xp] = _create_merge(xp, sampling)
            xp_design_matrices[xp] = SampledBasisFunctions.from_external_instrument_model(
                sampling, xp_merge[xp], instr_model)
    return xp_design_matrices, xp_merge


def _create_spectra(parsed_spectrum_file, truncation, design_matrices, merge):
    """
    Internal wrapper function. Allows _create_spectrum to use the generic
    progress tracker.
    """
    spectra_list = []
    nrows = len(parsed_spectrum_file)

    @_progress_tracker
    def create_spectrum(row, *args):
        truncation, design_matrices, merge = args[:3]
        spectrum = _create_spectrum(
            row, truncation, design_matrices, merge)
        spectra_list.append(spectrum)
    for index, row in parsed_spectrum_file.iterrows():
        create_spectrum(row, truncation, design_matrices, merge, index, nrows)
    return spectra_list


def _create_spectrum(row, truncation, design_matrix, merge):
    """
    Create a single sampled absolute spectrum from the input continuously-represented
    mean spectrum and design matrix.

    Args:
        row (DataFrame): Single row in a DataFrame containing the entry
            for one source in the mean spectra file. This will include columns for
            both bands (although one could be missing).
        truncation (bool): Toggle truncation of the set of bases.
        design_matrix (ndarray): 2D array containing the basis functions
            sampled on the pseudo-wavelength grid (either user-defined or default).
        merge (dict): Dictionary containing an array of weights per BP and one for RP.
            These have one value per sample and define the contributions from BP and RP
            to the joined absolute spectrum.

    Returns:
        AbsoluteSampledSpectrum: The sampled absolute spectrum.
    """
    source_id = row['source_id']
    cont_dict = {}
    # Split both bands
    for band in BANDS:
        try:
            covariance_matrix = _get_covariance_matrix(row, band)
            if covariance_matrix is not None:
                continuous_object = XpContinuousSpectrum(
                    source_id,
                    band,
                    row[f'{band}_coefficients'],
                    covariance_matrix,
                    row[f'{band}_standard_deviation'])
                cont_dict[band] = continuous_object
            if truncation:
                recommended_truncation = row[f'{band}_n_relevant_bases']
            else:
                recommended_truncation = -1
        except Exception:
            # If the band is not present, ignore it
            continue
    return AbsoluteSampledSpectrum(
        source_id, cont_dict, design_matrix, merge,
        truncation=recommended_truncation)
