"""
calibrator.py
====================================
Module for the calibrator functionality.
"""

from configparser import ConfigParser
from os.path import join
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
from tqdm import tqdm

from gaiaxpy.config.paths import config_path
from gaiaxpy.core.config import load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.core.generic_functions import cast_output, get_spectra_type, validate_arguments, validate_wl_sampling
from gaiaxpy.core.generic_variables import pbar_colour, pbar_units
from gaiaxpy.core.satellite import BANDS, BP_WL, RP_WL
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.output.sampled_spectra_data import SampledSpectraData
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.utils import get_covariance_matrix
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum
from .external_instrument_model import ExternalInstrumentModel

# Activate tqdm for pandas
tqdm.pandas(desc='Processing data', unit=pbar_units['calibrator'], leave=False, colour=pbar_colour)


def calibrate(input_object: Union[list, Path, str], sampling: np.ndarray = None, truncation: bool = False,
              output_path: Union[Path, str] = '.', output_file: str = 'output_spectra', output_format: str = None,
              save_file: bool = True, with_correlation: bool = False, username: str = None, password: str = None) -> \
        (pd.DataFrame, np.ndarray):
    """
    Calibration utility: calibrates the input internally-calibrated continuously-represented mean spectra to the
    absolute system. An absolute spectrum sampled on a user-defined or default wavelength grid is created for each set
    of BP and RP input spectra. If either band is missing, the output spectrum will only cover the range covered by the
    available data.

    Args:
        input_object (list/Path/str): Path to the file containing the mean spectra as downloaded from the archive in
            their continuous representation, a list of sources ids (string or long), or a pandas DataFrame.
        sampling (ndarray): 1D array containing the desired sampling in absolute wavelengths [nm].
        truncation (bool): Toggle truncation of the set of bases. The level of truncation to be applied is defined by
            the recommended value in the input files.
        output_path (Path/str): Path where to save the output data.
        output_file (str): Name of the output file without extension (e.g. 'my_file').
        output_format (str): Desired output format. If no format is given, the output file format will be the same as
            the input file (e.g. 'csv').
        save_file (bool): Whether to save the output in a file. If false, output_format and output_file will be ignored.
        with_correlation (bool): Whether correlation information should be generated.
        username (str): Cosmos username, only suggested when input_object is a list or ADQL query.
        password (str): Cosmos password, only suggested when input_object is a list or ADQL query.

    Returns:
        (tuple): tuple containing:

            DataFrame: The values for all sampled absolute spectra.
            ndarray: The sampling used to calibrate the input spectra (user-provided or default).
    """
    return _calibrate(input_object, sampling, truncation, output_path, output_file, output_format, save_file,
                      with_correlation=with_correlation, username=username, password=password)


def _calibrate(input_object: Union[list, Path, str], sampling: np.ndarray = None, truncation: bool = False,
               output_path: Union[Path, str] = '.', output_file: str = 'output_spectra', output_format: str = None,
               save_file: bool = True, with_correlation: bool = False, username: str = None, password: str = None,
               bp_model: str = 'v375wi', rp_model: str = 'v142r') -> (pd.DataFrame, np.ndarray):
    """
    Internal method of the calibration utility. Refer to "calibrate".

    Args:
        bp_model (str): The bp model.
        rp_model (str): The rp model.

    Returns:
        DataFrame: A list of all sampled absolute spectra.
        ndarray: The sampling used to calibrate the spectra.

    Raises:
        ValueError: If the sampling is out of the expected boundaries.
    """
    validate_wl_sampling(sampling)
    validate_arguments(_calibrate.__defaults__[3], output_file, save_file)
    parsed_input_data, extension = InputReader(input_object, _calibrate, username, password).read()
    xp_design_matrices, xp_merge = __generate_xp_matrices_and_merge('calibrator', sampling, bp_model, rp_model)
    spectra_df, positions = __create_spectra(parsed_input_data, truncation, xp_design_matrices, xp_merge,
                                             with_correlation=with_correlation)
    output_data = SampledSpectraData(spectra_df, positions)
    output_data.data = cast_output(output_data)
    # Save output
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return output_data.data, positions


def __create_merge(xp: str, sampling: np.ndarray) -> np.ndarray:
    """
    Create the weight information on the input sampling grid.

    Args:
        xp (str): Band (either 'bp' or 'rp').
        sampling (ndarray): 1D array containing the sampling grid.

    Returns:
        ndarray: A numpy array containing an array with weights for the given band.
    """
    if xp not in BANDS:
        raise ValueError(f"Band must be either 'bp' or 'rp'.")
    wl_high = BP_WL.high
    wl_low = RP_WL.low
    return np.array([1.0 if wl < wl_low else 0.0 if wl > wl_high else (1.0 - (wl - wl_low) / (wl_high - wl_low)) for
                     wl in sampling]) \
        if xp == BANDS.bp else np.array([0.0 if wl < wl_low else 1.0 if wl > wl_high else (wl - wl_low) /
                                                                                          (wl_high - wl_low)
                                         for wl in sampling])


def __generate_xp_matrices_and_merge(label: str, sampling: np.ndarray, bp_model: str, rp_model: str) -> (dict, dict):
    """
    Generates the xp_design_matrices and xp_merge from the input parameters.

    Args:
        label (str): The label for the data.
        sampling (np.ndarray): The given sampling.
        bp_model (str): The bp model.
        rp_model (str): The rp model.

    Returns:
        tuple: A tuple containing two dictionaries, one for the xp_design_matrices and the other for the xp_merge.
    """

    def __get_file_for_xp(xp: str, key: str, _bp_model: str = bp_model, _rp_model: str = rp_model) -> str:
        """
        Retrieves the file for the specified xp band.

        Args:
            xp (str): The xp band, either 'bp' or 'rp'.
            key (str): The key for the file in the config file.
            _bp_model (str): The bp model.
            _rp_model (str): The rp model.

        Returns:
            str: The file path for the specified xp band.

        Raises:
            ValueError: If the xp band is not 'bp' or 'rp'.
        """
        if xp not in BANDS:
            raise ValueError(f"Band must be either 'bp' or 'rp'.")
        config_parser = ConfigParser()
        config_parser.read(join(config_path, 'config.ini'))
        file_name = config_parser.get(label, key)
        model = _bp_model if xp == BANDS.bp else _rp_model
        return join(config_path, f"{file_name.replace('xp', xp).replace('model', model)}")

    if sampling is None:
        xp_sampling_grid, xp_merge = load_xpmerge_from_xml(bp_model=bp_model)
        xp_design_matrices = load_xpsampling_from_xml(bp_model=bp_model)
        xp_design_matrices = {xp: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_design_matrices[xp])
                              for xp in BANDS}
    else:
        xp_merge = {xp: __create_merge(xp, sampling) for xp in BANDS}
        xp_design_matrices = {xp: SampledBasisFunctions.from_external_instrument_model(
            sampling, xp_merge[xp], ExternalInstrumentModel.from_config_csv(
                __get_file_for_xp(xp, 'dispersion'), __get_file_for_xp(xp, 'response'), __get_file_for_xp(xp, 'bases')))
            for xp in BANDS}
    return xp_design_matrices, xp_merge


def __create_spectra(parsed_spectrum_file: pd.DataFrame, truncation: bool, design_matrices: dict, merge: dict,
                     with_correlation: bool = False):
    """
     Create a DataFrame of absolute sampled spectra for each source in the parsed mean spectra file.

     Args:
         parsed_spectrum_file (DataFrame): DataFrame containing information for each source in the mean spectra file.
             This includes columns for both bands (although one band could be missing).
         truncation (bool): If True, the set of bases is truncated.
         design_matrices (dict): Dictionary containing 2D arrays of basis functions sampled on the pseudo-wavelength
             grid (either user-defined or default) for both bands.
         merge (dict): Dictionary containing arrays of weights for both bands. These define the contributions from each
             band to the joined absolute spectrum.
         with_correlation (bool, optional): If True, the covariance information is included in the resulting
             AbsoluteSampledSpectrum objects. Defaults to False.

     Returns:
         tuple:
             spectra_df (DataFrame): DataFrame of absolute sampled spectra, each represented as a dictionary with
                 attributes 'data_type' indicating the type of spectra and 'positions' indicating the sample positions.
             positions (ndarray): 1D array of the sample positions.
     """
    spectra_series = parsed_spectrum_file.progress_apply(lambda row:
                                                         _create_spectrum(row, truncation, design_matrices, merge,
                                                                          with_correlation=with_correlation), axis=1)
    positions = spectra_series.iloc[0].get_positions()
    spectra_type = get_spectra_type(spectra_series.iloc[0])
    spectra_series = spectra_series.map(lambda x: x.spectrum_to_dict())
    spectra_df = pd.DataFrame(spectra_series.tolist())
    spectra_df.attrs['data_type'] = spectra_type
    return spectra_df, positions


def _create_spectrum(row, truncation, design_matrix, merge, with_correlation=False):
    """
    Create a single sampled absolute spectrum from the input continuously-represented mean spectrum and design matrix.

    Args:
        row (DataFrame): Single row in a DataFrame containing the entry for one source in the mean spectra file. This
            will include columns for both bands (although one could be missing).
        truncation (bool): Toggle truncation of the set of bases.
        design_matrix (ndarray): 2D array containing the basis functions sampled on the pseudo-wavelength grid (either
            user-defined or default).
        merge (dict): Dictionary containing an array of weights per BP and one for RP. These have one value per sample
            and define the contributions from BP and RP to the joined absolute spectrum.

    Returns:
        AbsoluteSampledSpectrum: The absolute sampled spectrum.
    """
    source_id = row['source_id']
    continuous_dict = dict()
    recommended_truncation = dict()
    # Split both bands
    for band in BANDS:
        covariance_matrix = get_covariance_matrix(row, band)
        if covariance_matrix is not None:
            continuous_dict[band] = XpContinuousSpectrum(source_id, band, row[f'{band}_coefficients'],
                                                         covariance_matrix, row[f'{band}_standard_deviation'])
        if truncation:
            recommended_truncation[band] = row[f'{band}_n_relevant_bases']
    return AbsoluteSampledSpectrum(source_id, continuous_dict, design_matrix, merge, truncation=recommended_truncation,
                                   with_correlation=with_correlation)  # An empty continuous dict will raise an error
