"""
converter.py
====================================
Module for the converter functionality.
"""

from numbers import Number
from pathlib import Path
from typing import Union, Optional

import numpy as np
import pandas as pd
from tqdm import tqdm

from gaiaxpy.core.generic_functions import cast_output, get_spectra_type, validate_arguments, validate_pwl_sampling
from gaiaxpy.core.generic_variables import pbar_colour, pbar_units, pbar_message
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.output.sampled_spectra_data import SampledSpectraData
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum
from gaiaxpy.spectrum.xp_sampled_spectrum import XpSampledSpectrum
from .config import get_config, load_config
from ..config.paths import optimised_bases_file

__FUNCTION_KEY = 'converter'


def convert(input_object: Union[list, Path, str], sampling: Optional[np.ndarray] = np.linspace(0, 60, 600),
            truncation: bool = False, with_correlation: bool = False, output_path: Union[Path, str] = '.',
            output_file: str = 'output_spectra', output_format: str = None, save_file: bool = True,
            username: str = None, password: str = None) -> (pd.DataFrame, np.ndarray):
    """
    Conversion utility: converts the input internally calibrated mean spectra from the continuous representation to a
        sampled form. The sampling grid can be defined by the user, alternatively a default will be adopted. Optionally,
        the continuous representation can be truncated dropping the bases functions (and corresponding coefficients)
        that were considered not to be significant considering the errors on the reconstructed mean spectra.

    Args:
        input_object (list/Path/str): Path to the file containing the mean spectra as downloaded from the archive in
            their continuous representation, a list of sources ids (string or long), or a pandas DataFrame.
        sampling (ndarray): 1D array containing the desired sampling in pseudo-wavelengths.
        truncation (bool): Toggle truncation of the set of bases. The level of truncation to be applied is defined by
            the recommended value in the input files.
        with_correlation (bool): Whether correlation information should be generated.
        output_path (Path/str): Path where to save the output data.
        output_file (str): Name of the output file without extension (e.g. 'my_file').
        output_format (str): Desired output format. If no format is given, the output file format will be the same as
            the input file (e.g. 'csv').
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
    return _convert(input_object=input_object, sampling=sampling, truncation=truncation,
                    with_correlation=with_correlation, output_path=output_path, output_file=output_file,
                    output_format=output_format, save_file=save_file, username=username, password=password)


def _convert(input_object: Union[list, Path, str], sampling: np.ndarray = np.linspace(0, 60, 600),
             truncation: bool = False, with_correlation: bool = False, output_path: Union[Path, str] = '.',
             output_file: str = 'output_spectra', output_format: str = None, save_file: bool = True,
             username: str = None, password: str = None, disable_info: bool = False) -> (pd.DataFrame, np.ndarray):
    """
    Internal method of the calibration utility. Refer to "convert".

    Args:
        disable_info (bool): Whether to disable the progress tracker.

    Returns:
        DataFrame: A list of all sampled absolute spectra.
        ndarray: The sampling used to calibrate the spectra.

    Raises:
        ValueError: If the sampling is out of the expected boundaries.
    """
    # Check sampling
    validate_pwl_sampling(sampling)
    validate_arguments(convert.__defaults__[4], output_file, save_file)
    parsed_input_data, extension = InputReader(input_object, convert, disable_info=disable_info, user=username,
                                               password=password).read()
    config_df = load_config(optimised_bases_file)
    # Union of unique ids as sets
    unique_bases_ids = get_unique_basis_ids(parsed_input_data)
    # Get design matrices
    design_matrices = get_design_matrices(unique_bases_ids, sampling, config_df)
    spectra_df, positions = _create_spectra(parsed_input_data, truncation, design_matrices,
                                            with_correlation=with_correlation, disable_info=disable_info)
    # Save output
    output_data = SampledSpectraData(spectra_df, positions)
    output_data.data = cast_output(output_data)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return output_data.data, positions


def _create_spectrum(row: pd.Series, truncation: bool, design_matrices: dict, band: str,
                     with_correlation: bool = False) -> XpSampledSpectrum:
    """
    Create a single sampled spectrum from the input continuously-represented mean spectrum and design matrix.

    Args:
        row (pd.Series): Single row in a DataFrame containing the entry for one source in the mean spectra file.
            This will include columns for both bands (although one could be missing).
        truncation (bool): Toggle truncation of the set of bases. The level of truncation to be applied is defined by
            the recommended value in the input files.
        design_matrices (dict): 2D array containing the basis functions sampled on the pseudo-wavelength grid (either
            user-defined or default).
        band (str): bp/rp band.
        with_correlation (bool): Whether correlation information should be generated.

    Returns:
        XpSampledSpectrum: The sampled spectrum.
    """
    covariance_matrix = row[f'{band}_covariance_matrix']
    recommended_truncation = row[f'{band}_n_relevant_bases'] if truncation else -1
    continuous_spectrum = XpContinuousSpectrum(row['source_id'], band, row[f'{band}_coefficients'],
                                               covariance_matrix, row[f'{band}_standard_deviation'])
    return XpSampledSpectrum.from_continuous(continuous_spectrum, design_matrices.get(row[f'{band}_basis_function_id']),
                                             truncation=recommended_truncation, with_correlation=with_correlation)


def _create_spectra(parsed_input_data: pd.DataFrame, truncation: bool, design_matrices: dict,
                    with_correlation: bool = False, disable_info=False) -> tuple:
    """
    Creates a spectra dataframe from parsed input data and given parameters.

    Args:
        parsed_input_data (pd.DataFrame): The parsed input data to create the spectra from.
        truncation (bool): Toggle truncation of the set of bases. The level of truncation to be applied is defined by
            the recommended value in the input files.
        design_matrices (dict): The design matrices for the input list of bases.
        with_correlation (bool): Whether to include the covariance matrix in the spectra. Default is False.

    Returns:
        (tuple): tuple containing:
            DataFrame: The output spectra.
            ndarray: The sampling used to convert the input spectra (user-provided or default).
    """
    def create_xp_spectra(row, _truncation, _design_matrices, _with_correlation=False):
        """
        Creates bp and rp spectra for a single row of parsed input data.

        Args:
            row (pandas Series): A single row of parsed input data.
            _truncation (bool): Toggle truncation of the set of bases. The level of truncation to be applied is defined
                by the recommended value in the input files.
            _design_matrices (dict): The design matrices for the input list of bases.
            _with_correlation (bool): Whether to include the covariance matrix in the spectra. Default is False.

        Returns:
            list: A list of spectra for the given row of parsed input data containing one element per band available.
        """
        spectra_list = []
        for band in BANDS:
            spectrum_xp = _create_spectrum(row, _truncation, _design_matrices, band, with_correlation=_with_correlation)
            if spectrum_xp:
                spectra_list.append(spectrum_xp)
        return spectra_list

    parsed_input_data_dict = parsed_input_data.to_dict('records')
    spectra_series = pd.Series([create_xp_spectra(row, truncation, design_matrices, with_correlation)
                                for row in tqdm(parsed_input_data_dict, desc=pbar_message[__FUNCTION_KEY],
                                                unit=pbar_units[__FUNCTION_KEY], leave=False, colour=pbar_colour,
                                                disable=disable_info)])
    spectra_series = spectra_series.explode()
    positions = spectra_series.iloc[0].get_positions()
    spectra_type = get_spectra_type(spectra_series.iloc[0])
    spectra_series = spectra_series.map(lambda x: x.spectrum_to_dict())
    spectra_df = pd.DataFrame(spectra_series.tolist())
    spectra_df.attrs['data_type'] = spectra_type
    return spectra_df, positions


def get_unique_basis_ids(parsed_input_data: pd.DataFrame) -> set:
    """
    Get the IDs of the unique basis required to sample all spectra in the input files.

    Args:
        parsed_input_data (DataFrame): Pandas DataFrame populated with the content of the file containing the mean
            spectra in continuous representation.

    Returns:
        set: A set containing all the required unique basis function IDs.
    """

    # Keep only non-NaN values (in Python, nan != nan)
    def remove_nans(_set):
        return {int(element) for element in _set if element == element}

    set_bp = set([basis for basis in parsed_input_data[f'{BANDS.bp}_basis_function_id'] if isinstance(basis, Number)])
    set_rp = set([basis for basis in parsed_input_data[f'{BANDS.rp}_basis_function_id'] if isinstance(basis, Number)])
    return remove_nans(set_bp).union(remove_nans(set_rp))


def get_design_matrices(unique_bases_ids: set, sampling: np.ndarray, config_df: pd.DataFrame) -> dict:
    """
    Get the design matrices corresponding to the input bases.

    Args:
        unique_bases_ids (set): A set containing the basis function IDs for which the design matrix is required.
        sampling (ndarray): 1D array containing the sampling grid.
        config_df (DataFrame): A DataFrame containing the configuration for all sets of basis functions.

    Returns:
        dict: The design matrices for the input list of bases.
    """
    return {_id: SampledBasisFunctions.from_config(sampling, get_config(config_df, _id)) for _id in unique_bases_ids}
