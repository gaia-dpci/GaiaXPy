"""
cholesky.py
====================================
Module that implements the Cholesky functionality.
"""

import pandas as pd
from numpy import diag, dot, identity
from scipy.linalg import cholesky, solve_triangular

from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader


def __get_dot_product(L_inv):
    try:
        return dot(L_inv.T, L_inv)
    except AttributeError:
        return None


def __get_inv_cholesky_decomp_lower(xp_errors, xp_correlation_matrix):
    try:
        L = cholesky(xp_correlation_matrix, lower=True)
        # Invert lower triangular matrix.
        L_inv = solve_triangular(L, identity(len(L)), lower=True)
        # Matrix of inverse errors.
        E_inv = diag(1.0 / xp_errors)
        return dot(L_inv, E_inv)
    except ValueError:
        return None


def get_inverse_covariance_matrix(input_object, band=None):
    """
    Compute the inverse covariance matrix.

    Args:
        input_object (object): Path to the file containing the mean spectra as downloaded from the archive in their
            continuous representation, a list of sources ids (string or long), or a pandas DataFrame.
        band (str): Chosen band: 'bp' or 'rp'. If no band is passed, the function will compute the inverse covariance
            for both 'bp' and 'rp'.

    Returns:
        DataFrame or ndarray: DataFrame containing the source IDs and the output inverse covariance matrices for the
            sources in the input object if it contains more than one source or no band is passed to the function.
            The function will return a ndarray (of shape (55, 55)) if there is only one source ID in the input data and
                a single band is selected.
    """
    parsed_input_data, extension = InputReader(input_object, get_inverse_covariance_matrix)._read()
    bands_output = []
    if band is None:
        bands_to_process = BANDS
        output_columns = ['source_id', 'bp_inverse_covariance', 'rp_inverse_covariance']
    else:
        bands_to_process = [band]
        output_columns = ['source_id', f'{band}_inverse_covariance']
    for xp in bands_to_process:
        xp_errors = parsed_input_data[f'{xp}_coefficient_errors']
        xp_correlation_matrix = parsed_input_data[f'{xp}_coefficient_correlations']
        L_inv_iterable = map(__get_inv_cholesky_decomp_lower, xp_errors, xp_correlation_matrix)
        band_output = map(__get_dot_product, L_inv_iterable)
        bands_output.append(band_output)
    output_list = [parsed_input_data['source_id']]
    for element in bands_output:
        output_list.append(element)
    output_df = pd.DataFrame(zip(*output_list), columns=output_columns)
    if len(bands_to_process) == 1 and len(output_df) == 1:
        return output_df[f'{band}_inverse_covariance'].iloc[0]
    else:
        return output_df


def get_chi2(L_inv, residuals):
    """
    Compute chi2 from given inverse Cholesky and a residual vector (= data - model). This function defines = inverse *
        residuals such that chi2 = |x|^2., which guarantees that chi2 >= 0.

    Args:
        L_inv (ndarray): Inverse Cholesky of the covariance as computed from the function get_inverse_covariance_matrix.
        residuals (ndarray): Difference between the observed coefficient vector and some model prediction of it.

    Returns:
        float: Chi-squared value.
    """
    if L_inv.shape != (55, 55):
        raise ValueError('Inverse covariance matrix shape must be (55, 55).')
    if residuals.shape != (55,):
        raise ValueError('Residuals shape must be (55,).')
    x = dot(L_inv.T, residuals)
    return dot(x.T, x)
