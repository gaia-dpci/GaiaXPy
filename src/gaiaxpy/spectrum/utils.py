"""Select coefficient covariance fields and reconstruct covariance from correlations."""

import numpy as np
import pandas as pd


def get_covariance_matrix(row, band):
    """Select or reconstruct the coefficient covariance for one source and band.

    Args:
        row (pandas.Series or namedtuple): One source row with fields accessible
            as attributes. Covariance fields take priority in this order:
            BAND_covariance_matrix, BAND_coefficient_covariances, then
            BAND_coefficient_correlations. The correlation branch also requires
            BAND_coefficient_errors and BAND_standard_deviation.
        band (str): Lowercase 'bp' or 'rp', replacing BAND in field names.

    Returns:
        numpy.ndarray or float: Stored covariance, or reconstructed covariance.
        A stored None becomes NaN.

    Raises:
        TypeError: The row type cannot be inspected.
        ValueError: None of the recognised covariance or correlation fields exists.
        AttributeError: A selected field is unavailable through attribute access,
            as with ordinary dictionary input.
    """
    if isinstance(row, pd.Series):
        columns = row.index
    elif hasattr(row, "_fields"):  # named tuple from DataFrame.itertuples()
        columns = row._fields
    else:
        raise TypeError(f'Input row is not of any of the input types {type(row).__name__}.')

    if f'{band}_covariance_matrix' in columns:
        covariance_matrix = getattr(row, f'{band}_covariance_matrix')
        return np.nan if covariance_matrix is None else covariance_matrix
    elif f'{band}_coefficient_covariances' in columns:
        coefficient_covariances = getattr(row, f'{band}_coefficient_covariances')
        return np.nan if coefficient_covariances is None else coefficient_covariances
    elif f'{band}_coefficient_correlations' in columns:
        return correlation_to_covariance_dr3int5(getattr(row, f'{band}_coefficient_correlations'),
                                                 getattr(row, f'{band}_coefficient_errors'),
                                                 getattr(row, f'{band}_standard_deviation'))
    raise ValueError(f'None of the expected columns could be found in the input row. Columns are: {columns}.')


def correlation_to_covariance_dr3int5(correlation_matrix, formal_errors, standard_deviation):
    """Reconstruct coefficient covariance using the same convention used since DR3.

    Args:
        correlation_matrix (numpy.ndarray): Full square correlation matrix.
        formal_errors (numpy.ndarray): One formal coefficient error per row.
        standard_deviation (float): Solution standard deviation used to
            normalise the coefficient errors.

    Returns:
        numpy.ndarray or float: D @ correlation_matrix @ D, where D is the
        diagonal matrix of formal_errors / standard_deviation. Returns NaN
        when standard_deviation is missing.
    """
    if pd.isna(standard_deviation):
        return np.nan

    correlation_matrix = np.asarray(correlation_matrix, dtype=np.float64)
    formal_errors = np.asarray(formal_errors, dtype=np.float64)
    diagonal_errors = np.diag(formal_errors / standard_deviation)

    return diagonal_errors @ correlation_matrix @ diagonal_errors


def _list_to_array(lst):
    """Convert a non-empty list to a NumPy array, preserving existing arrays.

    Args:
        lst (list, numpy.ndarray or None): Value to convert. A float NaN is
            treated as missing.

    Returns:
        numpy.ndarray or None: Original array, newly converted list, or None
        for a missing value.

    Raises:
        ValueError: A list is empty or the input type is unsupported. Existing
            NumPy arrays, including empty arrays, are returned unchanged.
    """
    if lst is None or (isinstance(lst, float) and pd.isna(lst)):
        return None
    if isinstance(lst, np.ndarray):
        return lst
    elif isinstance(lst, list):
        if not lst:
            raise ValueError('List cannot be empty.')
        else:
            return np.array(lst)
    raise ValueError('Wrong input type.')
