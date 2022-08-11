import pandas as pd
from numpy import diag, dot, identity
from scipy.linalg import cholesky, solve_triangular
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


def get_inverse_covariance_matrix(input_object=None, band=None):
    """
    Compute the inverse covariance matrix.

    Args:
        input_object (object): Path to the file containing the mean spectra
             as downloaded from the archive in their continuous representation,
             a list of sources ids (string or long), or a pandas DataFrame.
        band (str): Chosen band: 'bp' or 'rp'.

    Returns:
        DataFrame: DataFrame containing the source IDs and the output inverse
                   covariance matrices for the sources in the input object.
    """
    band = band.lower()
    parsed_input_data, extension = InputReader(input_object, get_inverse_covariance_matrix)._read()
    xp_errors = parsed_input_data[f'{band}_coefficient_errors']
    xp_correlation_matrix = parsed_input_data[f'{band}_coefficient_correlations']
    L_inv_iterable = map(__get_inv_cholesky_decomp_lower, xp_errors, xp_correlation_matrix)
    output = zip(parsed_input_data['source_id'], map(__get_dot_product, L_inv_iterable))
    return pd.DataFrame(output, columns=['source_id', f'{band}_inverse_covariance'])


def get_chi2(residuals, L_inv):
    x = dot(L_inv.T, residuals)
    return dot(x.T, x)
