"""
converter.py
====================================
Module for the converter functionality.
"""

import numbers
import numpy as np
import pandas as pd
from configparser import ConfigParser
from os import path
from .config import get_config, load_config
from gaiaxpy.config import config_path
from gaiaxpy.core import _get_spectra_type, _progress_tracker, \
                         _validate_arguments, _validate_pwl_sampling
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader import InputReader
from gaiaxpy.output import SampledSpectraData
from gaiaxpy.spectrum import SampledBasisFunctions, XpContinuousSpectrum, \
                             XpSampledSpectrum, _get_covariance_matrix

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))
config_file = path.join(config_path, config_parser.get('converter', 'optimised_bases'))


def convert(
        input_object,
        sampling=np.linspace(
            0,
            60,
            600),
        truncation=False,
        output_path='.',
        output_file='output_spectra',
        output_format=None,
        save_file=True,
        username=None,
        password=None):
    """
    Conversion utility: converts the input internally calibrated mean
    spectra from the continuous representation to a sampled form. The
    sampling grid can be defined by the user, alternatively a default
    will be adopted. Optionally, the continuous representation can be
    truncated dropping the bases functions (and corresponding coefficients)
    that were considered not to be significant considering the errors
    on the reconstructed mean spectra.

    Args:
        input_object (object): Path to the file containing the mean spectra
             as downloaded from the archive in their continuous representation,
             a list of sources ids (string or long), or a pandas DataFrame.
        sampling (ndarray): 1D array containing the desired sampling in
             pseudo-wavelengths.
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
            DataFrame: The values for all sampled spectra.
            ndarray: The sampling used to convert the input spectra (user-provided or default).

    Raises:
        ValueError: If the sampling is out of the expected boundaries.
    """
    # Check sampling
    _validate_pwl_sampling(sampling)
    _validate_arguments(convert.__defaults__[3], output_file, save_file)
    parsed_input_data, extension = InputReader(input_object, convert, username, password)._read()
    config_df = load_config(config_file)
    # Union of unique ids as sets
    unique_bases_ids = get_unique_basis_ids(parsed_input_data)
    # Get design matrices
    design_matrices = get_design_matrices(unique_bases_ids, sampling, config_df)
    spectra_list = _create_spectra(parsed_input_data, truncation, design_matrices)
    # Generate output
    spectra_df = pd.DataFrame.from_records([spectrum._spectrum_to_dict() for spectrum in spectra_list])
    spectra_type = _get_spectra_type(spectra_list)
    spectra_df.attrs['data_type'] = spectra_type
    positions = spectra_list[0]._get_positions()
    # Save output
    output_data = SampledSpectraData(spectra_df, positions)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return spectra_df, positions


def _create_continuous_spectrum(row, band):
    covariance_matrix = _get_covariance_matrix(row, band)
    if covariance_matrix is not None:
        continuous_spectrum = XpContinuousSpectrum(
            row['source_id'],
            band.upper(),
            row[f'{band}_coefficients'],
            covariance_matrix,
            row[f'{band}_standard_deviation'])
        return continuous_spectrum


def _create_spectrum(row, truncation, design_matrices, band):
    """
    Create a single sampled spectrum from the input continuously-represented
    mean spectrum and design matrix.

    Args:
        row (DataFrame): Single row in a DataFrame containing the entry
            for one source in the mean spectra file. This will include columns for
            both bands (although one could be missing).
        truncation (bool): Toggle truncation of the set of bases.
        design_matrix (ndarray): 2D array containing the basis functions
            sampled on the pseudo-wavelength grid (either user-defined or default).
        band (str): BP/RP band.

    Returns:
        obj: The sampled spectrum.
    """
    covariance_matrix = _get_covariance_matrix(row, band)
    if covariance_matrix is not None:
        continuous_spectrum = XpContinuousSpectrum(
            row['source_id'],
            band,
            row[f'{band}_coefficients'],
            covariance_matrix,
            row[f'{band}_standard_deviation'])
    if truncation:
        recommended_truncation = row[f'{band}_n_relevant_bases']
    else:
        recommended_truncation = -1
    spectrum = XpSampledSpectrum.from_continuous(
        continuous_spectrum,
        design_matrices.get(
            row.loc[f'{band}_basis_function_id']),
        truncation=recommended_truncation)
    return spectrum


def _create_spectra(parsed_input_data, truncation, design_matrices):
    """
    Internal wrapper function. Allows _create_spectrum to use the generic
    progress tracker.
    """
    spectra_list = []
    nrows = len(parsed_input_data)

    @_progress_tracker
    def create_spectrum(row, truncation, *args):
        design_matrices = args[0]
        for band in BANDS:
            try:
                spectrum_xp = _create_spectrum(row, truncation, design_matrices, band)
                spectra_list.append(spectrum_xp)
            except BaseException:
                # Band not available
                continue
    for index, row in parsed_input_data.iterrows():
        create_spectrum(row, truncation, design_matrices, index, nrows)
    return spectra_list


def get_unique_basis_ids(parsed_input_data):
    """
    Get the IDs of the unique basis required to sample all spectra in the input files.

    Args:
        parsed_input_data (DataFrame): Pandas DataFrame populated with the content
            of the file containing the mean spectra in continuous representation.

    Returns:
        set: A set containing all the required unique basis function IDs.
    """
    # Keep only non NaN values (in Python, nan != nan)
    def remove_nans(_set):
        return {int(element) for element in _set if element == element}

    set_bp = set([basis for basis in parsed_input_data[f'{BANDS.bp}_basis_function_id'] if isinstance(basis, numbers.Number)])
    set_rp = set([basis for basis in parsed_input_data[f'{BANDS.rp}_basis_function_id'] if isinstance(basis, numbers.Number)])
    return remove_nans(set_bp).union(remove_nans(set_rp))


def get_design_matrices(unique_bases_ids, sampling, config_df):
    """
    Get the design matrices corresponding to the input bases.

    Args:
        unique_bases_ids (set): A set containing the basis function IDs
            for which the design matrix is required.
        sampling (ndarray): 1D array containing the sampling grid.
        config_df (DataFrame): A DataFrame containing the configuration for
            all sets of basis functions.

    Returns:
        list: a list of the design matrices for the input list of bases.
    """
    design_matrices = {}
    for id in unique_bases_ids:
        design_matrices.update({id: SampledBasisFunctions.from_config(
            sampling, get_config(config_df, id))})
    return design_matrices
