"""
utils.py
====================================
Module to hold methods useful for different kinds of spectra.
"""

import numpy as np


def _get_covariance_matrix(row, band):
    try:
        return _correlation_to_covariance_dr3int5(
            row[f'{band}_coefficient_correlations'],
            row[f'{band}_coefficient_errors'],
            row[f'{band}_standard_deviation'])
    except BaseException:
        try:
            # It is AVRO
            return row[f'{band}_coefficient_covariances']
        except BaseException:
            # Row may not be present
            return None


def _correlation_to_covariance_dr3int5(
        correlation_matrix,
        formal_errors,
        standard_deviation):
    """
    Compute the covariance matrix from the correlation matrix and the parameter formal errors.

    Args:
        correlation_matrix (ndarray of ndarrays): Correlation matrix.
        formal_errors (ndarray): Formal errors of the parameters.
        standard_deviation (float): Standard deviation of the LSQ solution.

    Returns:
        ndarray: The covariance matrix as a numpy array.
    """
    # Populate the diagonal matrix containing the formal errors.
    # In dr3int5 the errors have been scaled by the standard deviation. So to bring them back to what they were in dr3int3
    # I have to divide by the standard deviation.
    diagonal_errors = np.diag(formal_errors) / standard_deviation
    covariance_matrix = diagonal_errors.dot(
        correlation_matrix).dot(diagonal_errors)
    return covariance_matrix


def _correlation_to_covariance_dr3int4(
        correlation_matrix,
        formal_errors,
        standard_deviation):
    """
    Compute the covariance matrix from the correlation matrix and the parameter formal errors.

    Args:
        correlation_matrix (ndarray of ndarrays): Correlation matrix.
        formal_errors (ndarray): Formal errors of the parameters.
        standard_deviation (float): Standard deviation of the LSQ solution.

    Returns:
        ndarray: The covariance matrix as a numpy array.
    """
    # Populate the diagonal matrix containing the formal errors.
    # In dr3int4 the errors have been scaled by the standard deviation. So to bring them back to what they were in dr3int3
    # I have to divide by the standard deviation.
    diagonal_errors = np.diag(formal_errors) / standard_deviation
    # In dr3int4 the errors have been scaled by the standard deviation before the correlation matrix was computed. Adding
    # the following line to undo this.
    correlation_matrix_aux = np.multiply(correlation_matrix, (standard_deviation * standard_deviation))
    # In the CU9 files, only unique elements of this symmetric matrix are stored (without diagonal, as the diagonal of a
    # correlation matrix is supposed to be one). However the scaling at the previous line, changes the value of the
    # diagonal so that they are not 1 any more! They need to be reset to be 1.0.
    np.fill_diagonal(correlation_matrix_aux, 1.)
    covariance_matrix = diagonal_errors.dot(
        correlation_matrix_aux).dot(diagonal_errors)
    return covariance_matrix


def _correlation_to_covariance_dr3int3(
        correlation_matrix,
        formal_errors,
        standard_deviation):
    """
    Compute the covariance matrix from the correlation matrix and the parameter formal errors.

    Args:
        correlation_matrix (ndarray of ndarrays): Correlation matrix.
        formal_errors (ndarray): Formal errors of the parameters.
        standard_deviation (float): Standard deviation of the LSQ solution.

    Returns:
        ndarray: The covariance matrix as a numpy array.
    """
    # Populate the diagonal matrix containing the formal errors.
    diagonal_errors = np.diag(formal_errors)
    covariance_matrix = diagonal_errors.dot(
        correlation_matrix).dot(diagonal_errors)
    return covariance_matrix


def _list_to_array(lst):
    """
    List to NumPy array.
    """
    return np.array(lst)
