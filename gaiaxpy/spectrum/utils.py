"""
utils.py
====================================
Module to hold methods useful for different kinds of spectra.
"""

import numpy as np


def _get_covariance_matrix(row, band):
    try:
        return _correlation_to_covariance_dr3int5(row[f'{band}_coefficient_correlations'],
                                                  row[f'{band}_coefficient_errors'],
                                                  row[f'{band}_standard_deviation'])
    except BaseException as err:
        try:
            # It is AVRO
            return row[f'{band}_coefficient_covariances']
        except BaseException:
            # Row may not be present
            return None


def _correlation_to_covariance_dr3int5(correlation_matrix, formal_errors, standard_deviation):
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
    covariance_matrix = diagonal_errors.dot(correlation_matrix).dot(diagonal_errors)
    return covariance_matrix


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
    covariance_matrix = diagonal_errors.dot(correlation_matrix_aux).dot(diagonal_errors)
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
    covariance_matrix = diagonal_errors.dot(correlation_matrix).dot(diagonal_errors)
    return covariance_matrix


def _list_to_array(lst):
    """
    List to NumPy array.
    """
    return np.array(lst)
