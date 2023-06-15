"""
utils.py
====================================
Module to hold methods useful for different kinds of spectra.
"""

import numpy as np
import pandas as pd


def get_covariance_matrix(row, band):
    columns = row.keys() if isinstance(row, dict) else row.index
    if f'{band}_covariance_matrix' in columns:
        return row[f'{band}_covariance_matrix']
    elif f'{band}_coefficient_covariances' in columns:
        return row[f'{band}_coefficient_covariances']
    elif f'{band}_coefficient_correlations' in columns:
        return _correlation_to_covariance_dr3int5(row[f'{band}_coefficient_correlations'],
                                                  row[f'{band}_coefficient_errors'],
                                                  row[f'{band}_standard_deviation'])
    raise ValueError(f'None of the expected columns could be found in the input row. Columns are: {columns}.')


def _correlation_to_covariance_dr3int5(correlation_matrix, formal_errors, standard_deviation):
    """
    Compute the covariance matrix from the correlation matrix and the parameter formal errors.

    Args:
        correlation_matrix (ndarray): Correlation matrix, 2D array.
        formal_errors (ndarray): Formal errors of the parameters.
        standard_deviation (float): Standard deviation of the LSQ solution.

    Returns:
        ndarray: The covariance matrix as a numpy array.
    """
    if pd.isna(standard_deviation):
        return None
    diagonal_errors = np.diag(formal_errors) / standard_deviation
    return diagonal_errors @ correlation_matrix @ diagonal_errors


def _correlation_to_covariance_dr3int4(correlation_matrix, formal_errors, standard_deviation):
    """
    Compute the covariance matrix from the correlation matrix and the parameter formal errors.

    Args:
        correlation_matrix (ndarray): Correlation matrix.
        formal_errors (ndarray): Formal errors of the parameters.
        standard_deviation (float): Standard deviation of the LSQ solution.

    Returns:
        ndarray: The covariance matrix as a numpy array.
    """
    diagonal_errors = np.diag(formal_errors) / standard_deviation
    correlation_matrix_aux = np.multiply(correlation_matrix, (standard_deviation * standard_deviation))
    np.fill_diagonal(correlation_matrix_aux, 1.)
    covariance_matrix = diagonal_errors @ correlation_matrix_aux @ diagonal_errors
    return covariance_matrix


def _correlation_to_covariance_dr3int3(correlation_matrix, formal_errors):
    """
    Compute the covariance matrix from the correlation matrix and the parameter formal errors.

    Args:
        correlation_matrix (ndarray): Correlation matrix.
        formal_errors (ndarray): Formal errors of the parameters.

    Returns:
        ndarray: The covariance matrix as a numpy array.
    """
    # Populate the diagonal matrix containing the formal errors.
    diagonal_errors = np.diag(formal_errors)
    covariance_matrix = diagonal_errors @ correlation_matrix @ diagonal_errors
    return covariance_matrix


def _list_to_array(lst):
    """
    List to NumPy array.
    """
    if isinstance(lst, np.ndarray):
        return lst
    elif isinstance(lst, list):
        if not lst:
            raise ValueError('List cannot be empty.')
        else:
            return np.array(lst)
    raise ValueError('Wrong input type.')
