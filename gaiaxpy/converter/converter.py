"""
converter.py
====================================
Module for the converter functionality.
"""

from configparser import ConfigParser
from numbers import Number
from os import path

import numpy as np
import pandas as pd
from tqdm import tqdm

from gaiaxpy.config.paths import config_path
from gaiaxpy.core.generic_functions import cast_output, _get_spectra_type, _validate_arguments, _validate_pwl_sampling
from gaiaxpy.core.generic_variables import pbar_colour, pbar_units
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.output.sampled_spectra_data import SampledSpectraData
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.utils import _get_covariance_matrix
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum
from gaiaxpy.spectrum.xp_sampled_spectrum import XpSampledSpectrum
from .config import get_config, load_config

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))
config_file = path.join(config_path, config_parser.get('converter', 'optimised_bases'))
# Activate tqdm for pandas
tqdm.pandas(desc='Processing data', unit=pbar_units['converter'], leave=False, colour=pbar_colour)


def convert(input_object, sampling=np.linspace(0, 60, 600), truncation=False, output_path='.',
            output_file='output_spectra', output_format=None, save_file=True, username=None, password=None):
    """
    Conversion utility: converts the input internally calibrated mean spectra from the continuous representation to a
    sampled form. The sampling grid can be defined by the user, alternatively a default will be adopted. Optionally,
    the continuous representation can be truncated dropping the bases functions (and corresponding coefficients) that
    were considered not to be significant considering the errors on the reconstructed mean spectra.

    Args:
        input_object (object): Path to the file containing the mean spectra as downloaded from the archive in their
            continuous representation, a list of sources ids (string or long), or a pandas DataFrame.
        sampling (ndarray): 1D array containing the desired sampling in pseudo-wavelengths.
        truncation (bool): Toggle truncation of the set of bases. The level of truncation to be applied is defined by
            the recommended value in the input files.
        output_path (str): Path where to save the output data.
        output_file (str): Name of the output file.
        output_format (str): Format to be used for the output file. If no format is given, then the output file will be
            in the same format as the input file.
        save_file (bool): Whether to save the output in a file. If false, output_format and output_file will be ignored.
        username (str): Cosmos username, only suggested when input_object is a list or ADQL query.
        password (str): Cosmos password, only suggested when input_object is a list or ADQL query.

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
    spectra_df, positions = _create_spectra(parsed_input_data, truncation, design_matrices)
    # Save output
    output_data = SampledSpectraData(spectra_df, positions)
    output_data.data = cast_output(output_data)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return spectra_df, positions


def _create_continuous_spectrum(row, band):
    covariance_matrix = _get_covariance_matrix(row, band)
    if covariance_matrix is not None:
        continuous_spectrum = XpContinuousSpectrum(row['source_id'], band.upper(), row[f'{band}_coefficients'],
                                                   covariance_matrix, row[f'{band}_standard_deviation'])
        return continuous_spectrum


def _create_spectrum(row, truncation, design_matrices, band):
    """
    Create a single sampled spectrum from the input continuously-represented mean spectrum and design matrix.

    Args:
        row (DataFrame): Single row in a DataFrame containing the entry for one source in the mean spectra file. This
            will include columns for both bands (although one could be missing).
        truncation (bool): Toggle truncation of the set of bases.
        design_matrices (ndarray): 2D array containing the basis functions sampled on the pseudo-wavelength grid (either
            user-defined or default).
        band (str): BP/RP band.

    Returns:
        obj: The sampled spectrum.
    """
    covariance_matrix = _get_covariance_matrix(row, band)
    if covariance_matrix is not None:
        continuous_spectrum = XpContinuousSpectrum(row['source_id'], band, row[f'{band}_coefficients'],
                                                   covariance_matrix, row[f'{band}_standard_deviation'])
    recommended_truncation = row[f'{band}_n_relevant_bases'] if truncation else -1
    spectrum = XpSampledSpectrum.from_continuous(continuous_spectrum, design_matrices.get(
        row.loc[f'{band}_basis_function_id']), truncation=recommended_truncation)
    return spectrum


def _create_spectra(parsed_input_data, truncation, design_matrices):
    def create_xp_spectra(row, _truncation, _design_matrices):
        spectra_list = []
        for band in BANDS:
            try:
                spectrum_xp = _create_spectrum(row, _truncation, _design_matrices, band)
            except BaseException:
                # Band not available
                continue
            spectra_list.append(spectrum_xp)
        return spectra_list

    spectra_series = parsed_input_data.progress_apply(lambda row: create_xp_spectra(row, truncation, design_matrices),
                                                      axis=1)
    spectra_df = spectra_series.to_frame()
    spectra_df = spectra_df.explode(0)  # Explode spectra column
    positions = spectra_df[0].iloc[0]._get_positions()
    spectra_type = _get_spectra_type(spectra_df[0].iloc[0])
    spectra_df[0] = spectra_df[0].progress_apply(lambda s: s._spectrum_to_dict())
    spectra_df = spectra_df[0].apply(pd.Series).reset_index(drop=True)
    spectra_df.attrs['data_type'] = spectra_type
    return spectra_df, positions


def get_unique_basis_ids(parsed_input_data):
    """
    Get the IDs of the unique basis required to sample all spectra in the input files.

    Args:
        parsed_input_data (DataFrame): Pandas DataFrame populated with the content of the file containing the mean
            spectra in continuous representation.

    Returns:
        set: A set containing all the required unique basis function IDs.
    """

    # Keep only non NaN values (in Python, nan != nan)
    def remove_nans(_set):
        return {int(element) for element in _set if element == element}

    set_bp = set([basis for basis in parsed_input_data[f'{BANDS.bp}_basis_function_id'] if isinstance(basis, Number)])
    set_rp = set([basis for basis in parsed_input_data[f'{BANDS.rp}_basis_function_id'] if isinstance(basis, Number)])
    return remove_nans(set_bp).union(remove_nans(set_rp))


def get_design_matrices(unique_bases_ids, sampling, config_df):
    """
    Get the design matrices corresponding to the input bases.

    Args:
        unique_bases_ids (set): A set containing the basis function IDs for which the design matrix is required.
        sampling (ndarray): 1D array containing the sampling grid.
        config_df (DataFrame): A DataFrame containing the configuration for all sets of basis functions.

    Returns:
        list: a list of the design matrices for the input list of bases.
    """
    return {_id: SampledBasisFunctions.from_config(sampling, get_config(config_df, _id)) for _id in unique_bases_ids}
