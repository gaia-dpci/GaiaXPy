"""
cholesky.py
====================================
Module that implements the Cholesky functionality.
"""
from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd
from numpy import diag, dot, identity
from scipy.linalg import cholesky, solve_triangular

from gaiaxpy.core.generic_functions import parse_band
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader


def __get_dot_product(_L_inv: np.ndarray) -> Optional[np.ndarray]:
    """
    Calculate the dot product of the transpose of L_inv with itself.

    Args:
        _L_inv (ndarray): A 2D numpy array.

    Returns:
        ndarray: The dot product of the transpose of L_inv with itself. None: If L_inv does not have the attribute `T`
            (transpose).
    """
    try:
        return dot(_L_inv.T, _L_inv)
    except AttributeError:
        return None


def __output_list_to_df(parsed_input_data: pd.DataFrame, bands_output: list, output_columns: list) -> pd.DataFrame:
    """
    Convert a list of output data into a pandas DataFrame.

    Args:
        parsed_input_data (pd.Dataframe): Parsed initial data.
        bands_output (list): A list of output data, where each element is a list of values for a specific band.
        output_columns (list): A list of strings representing the column names for the output DataFrame.

    Returns:
        pd.DataFrame: A DataFrame containing the source ID and the output data for each band.
    """
    output_list = [parsed_input_data['source_id']]
    for element in bands_output:
        output_list.append(element)
    return pd.DataFrame(zip(*output_list), columns=output_columns)


def get_inverse_square_root_covariance_matrix(input_object: Union[list, Path, str],
                                              band: Optional[Union[list, str]] = None):
    """
    Compute the inverse square root covariance matrix.

    Args:
        input_object (list/Path/str): Path to the file containing the mean spectra as downloaded from the archive in
            their continuous representation, a pandas DataFrame, a list of sources ids (string or long), or an ADQL
            query.
        band (str): Chosen band: 'bp' or 'rp'. If no band is passed, the function will compute the inverse square root
            covariance for both 'bp' and 'rp'.

    Returns:
        DataFrame or ndarray: DataFrame containing the source IDs and the output inverse square root covariance matrices
            for the sources in the input object if it contains more than one source or no band is passed to the
            function.
            The function will return a ndarray (of shape (55, 55)) if there is only one source ID in the input data
            and a single band is selected.
    """
    if band is not None:
        band = parse_band(band)
    parsed_input_data, extension = InputReader(input_object, get_inverse_square_root_covariance_matrix).read()
    if band is None:
        bands_to_process = BANDS
        output_columns = ['source_id', 'bp_inverse_square_root_covariance_matrix',
                          'rp_inverse_square_root_covariance_matrix']
    else:
        bands_to_process = [band]
        output_columns = ['source_id', f'{band}_inverse_square_root_covariance_matrix']
    bands_output = []
    for b in bands_to_process:
        xp_errors = parsed_input_data[f'{b}_coefficient_errors'] / parsed_input_data[f'{b}_standard_deviation']
        xp_correlation_matrix = parsed_input_data[f'{b}_coefficient_correlations']
        band_inv_iterable = map(_get_inverse_square_root_covariance_matrix_aux, xp_errors, xp_correlation_matrix)
        bands_output.append(band_inv_iterable)
    output_df = __output_list_to_df(parsed_input_data, bands_output, output_columns)
    if len(bands_to_process) == 1 and len(output_df) == 1:
        return output_df[f'{band}_inverse_square_root_covariance_matrix'].iloc[0]
    else:
        return output_df


def _get_inverse_square_root_covariance_matrix_aux(xp_errors: np.ndarray, xp_correlation_matrix: np.ndarray) -> \
        Optional[np.ndarray]:
    """
    Calculate the inverse square root of the covariance matrix.

    Args:
        xp_errors (ndarray): A numpy array representing the measurement errors.
        xp_correlation_matrix (ndarray): A numpy array representing the correlation matrix.

    Returns:
        ndarray: The inverse square root of the covariance matrix. None: If the Cholesky decomposition of the
            correlation matrix fails.
    """
    try:
        _L = cholesky(xp_correlation_matrix, lower=True)
        # Invert lower triangular matrix
        _L_inv = solve_triangular(_L, identity(len(_L)), lower=True)
        # Matrix of inverse errors
        _E_inv = diag(1.0 / xp_errors)
        return dot(_L_inv, _E_inv)
    except ValueError:
        return None


def get_inverse_covariance_matrix(input_object: Union[list, Path, str], band: str = None):
    """
    Compute the inverse covariance matrix.

    Args:
        input_object (object): Path to the file containing the mean spectra as downloaded from the archive in their
            continuous representation, a pandas DataFrame, a list of sources ids (string or long), or an ADQL query.
        band (str): Chosen band: 'bp' or 'rp'. If no band is passed, the function will compute the inverse covariance
            for both 'bp' and 'rp'.

    Returns:
        DataFrame or ndarray: DataFrame containing the source IDs and the output inverse covariance matrices for the
            sources in the input object if it contains more than one source or no band is passed to the function.
            The function will return a ndarray (of shape (55, 55)) if there is only one source ID in the input data
            and a single band is selected.
    """
    band = band if band is None else parse_band(band)
    parsed_input_data, extension = InputReader(input_object, get_inverse_covariance_matrix).read()
    bands_output = []
    if band is None:
        bands_to_process = BANDS
        output_columns = ['source_id', 'bp_inverse_covariance', 'rp_inverse_covariance']
    else:
        bands_to_process = [band]
        output_columns = ['source_id', f'{band}_inverse_covariance']
    for b in bands_to_process:
        # The formal errors need to be scaled by the inverse standard deviation.
        xp_errors = parsed_input_data[f'{b}_coefficient_errors'] / parsed_input_data[f'{b}_standard_deviation']
        xp_correlation_matrix = parsed_input_data[f'{b}_coefficient_correlations']
        _L_inv_iterable = map(_get_inverse_square_root_covariance_matrix_aux, xp_errors, xp_correlation_matrix)
        band_output = map(__get_dot_product, _L_inv_iterable)
        bands_output.append(band_output)
    output_df = __output_list_to_df(parsed_input_data, bands_output, output_columns)
    if len(bands_to_process) == 1 and len(output_df) == 1:
        return output_df[f'{band}_inverse_covariance'].iloc[0]
    else:
        return output_df


def get_chi2(_L_inv: np.ndarray, residuals: np.ndarray) -> np.ndarray:
    """
    Compute chi-squared (chi2) from given inverse Cholesky of the covariance matrix (L^-1) and a residual vector
    (r = data - model). This function defines x = L^-1 * r such that chi2 = |x|^2, which guarantees that chi2 >= 0.

    Args:
        _L_inv (ndarray): Inverse square root of the covariance, as computed from the function
            get_inverse_square_root_covariance_matrix.
        residuals (ndarray): Difference between the observed coefficient vector and some model prediction of it.

    Returns:
        float: Chi-squared value.
    """
    if _L_inv is None or residuals is None:  # Cannot be checked with 'not' as the truth value of an array is ambiguous.
        raise ValueError('Input parameters cannot be None.')
    if _L_inv.shape != (55, 55):
        raise ValueError('Inverse covariance matrix shape must be (55, 55).')
    if residuals.shape != (55,):
        raise ValueError('Residuals shape must be (55,).')
    x = dot(_L_inv, residuals)
    return dot(x.T, x)
