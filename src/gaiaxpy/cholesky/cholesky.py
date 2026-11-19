"""Use Cholesky factorisation to weight continuous-spectrum coefficient residuals.

For each source and photometer, let D contain coefficient_errors divided by
standard_deviation on its diagonal, and let R be the coefficient correlation
matrix. These functions use C = D @ R @ D. If R = L @ L.T is its correlation
factorisation, the returned inverse Cholesky factor of C is
W = inv(D @ L) = inv(L) @ inv(D).
Then W.T @ W = inv(C), and chi-squared is the squared norm of W @ residuals.

This inverse-square-root convention gives a lower-triangular matrix rather
than the symmetric inverse square root of C. No truncation is applied and
results are returned in memory without saving output files.
"""
from pathlib import Path
from typing import Optional, Union

import numpy as np
from numpy import diag, dot, identity
from scipy.linalg import cholesky, solve_triangular

from gaiaxpy.core.generic_functions import parse_band
from gaiaxpy.core.release_resolution import parse_release
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader


def __get_dot_product(_lower_inv: np.ndarray) -> Optional[np.ndarray]:
    """Compute the inverse covariance W.T @ W from its inverse Cholesky factor W.

    Args:
        _lower_inv (numpy.ndarray or None): Inverse lower Cholesky factor of the
            covariance, or None for a source/photometer without a result.

    Returns:
        numpy.ndarray or None: Matrix product, or None if the supplied object
        has no transpose attribute. Other matrix-operation errors are reported
        to the caller.
    """
    try:
        return dot(_lower_inv.T, _lower_inv)
    except AttributeError:
        return None


def __output_list_to_df(parsed_input_data: 'pd.DataFrame', bands_output: list, output_columns: list) -> 'pd.DataFrame':
    """Combine source identifiers and per-photometer matrix iterables into a table.

    Args:
        parsed_input_data (pandas.DataFrame): Prepared table containing source_id.
        bands_output (list): One iterable of matrices or None entries per
            selected photometer, in input row order.
        output_columns (list[str]): source_id followed by a name for each
            photometer's output.

    Returns:
        pandas.DataFrame: Source identifiers and matrix-valued columns with
        a default integer index.
    """
    from pandas import DataFrame as pdDf
    output_list = [parsed_input_data['source_id']] + bands_output
    return pdDf(zip(*output_list, strict=True), columns=output_columns)


def get_inverse_square_root_covariance_matrix(input_object: Union[list, Path, 'pd.DataFrame', str],
                                              band: Optional[str] = None, release: str | None = None) \
        -> (Union)['pd.DataFrame', np.ndarray]:
    """Compute the inverse Cholesky factor of each selected coefficient covariance.

    Args:
        input_object (str, pathlib.Path, pandas.DataFrame, list or tuple): Input
            continuous BP/RP mean spectra. Supply a local file, a DataFrame,
            a list or tuple of integer source IDs, or an ADQL query. Supported local
            formats include CSV, ECSV, FITS and XML/VOTable, gzip inputs and
            Archive ZIP files. Source-ID selections and queries retrieve Archive
            spectra. InputReader requires its usual continuous-spectrum fields
            for both photometers, including coefficient error information and
            standard deviations, even when one photometer is selected here.
        band (str or None): 'bp' or 'rp', ignoring case. None, the default,
            computes both photometers independently.
        release (str or None): Gaia release. Defaults to 'dr3' when not specified.
            When identifiable, the input release must match the selected release.

    Returns:
        pandas.DataFrame, numpy.ndarray or None: With exactly one input row and
        one selected photometer, return its inverse Cholesky factor directly,
        or None when its factorisation cannot be computed. Otherwise, return
        source_id and bp_inverse_square_root_covariance_matrix and/or
        rp_inverse_square_root_covariance_matrix columns. Each cell contains
        a matrix or None; rows follow the prepared input order. Matrix dimensions
        match the number of coefficients for that photometer and release.

    Raises:
        InvalidBandError: A supplied band is unsupported.
        InvalidReleaseError: A supplied release is unsupported.
        ValueError: Required input fields are missing, or supplied and
            detected releases disagree.
    """
    release = parse_release(release)
    if band is not None:
        band = parse_band(band)
    parsed_input_data, extension, release = InputReader(input_object, get_inverse_square_root_covariance_matrix,
                                                        truncation=False, release=release).read()
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
    """Compute an inverse Cholesky factor from scaled errors and correlations.

    Args:
        xp_errors (numpy.ndarray): One-dimensional coefficient-error vector
            after division by the photometer's standard_deviation.
        xp_correlation_matrix (numpy.ndarray): Corresponding square correlation
            matrix, expected to be symmetric and positive definite.

    Returns:
        numpy.ndarray or None: inv(L) @ diag(1 / xp_errors), where L is the
        lower Cholesky factor of the correlation matrix. Return None when
        factorisation, triangular solving or subsequent operations raise
        ValueError, including a non-positive-definite correlation matrix.

    Notes:
        Uses the lower triangle for Cholesky factorisation. No separate symmetry
        check is performed. Zero errors are not rejected before division and
        can produce non-finite results. Other exception types reach the caller.
    """
    try:
        _lower = cholesky(xp_correlation_matrix, lower=True)
        # Invert lower triangular matrix
        _lower_inv = solve_triangular(_lower, identity(len(_lower)), lower=True)
        # Matrix of inverse errors
        _error_inv = diag(1.0 / xp_errors)
        return dot(_lower_inv, _error_inv)
    except ValueError:
        return None


def get_inverse_covariance_matrix(input_object: Union[list, Path, 'pd.DataFrame', str], band: Optional[str] = None,
                                  release: str | None = None) -> 'pd.DataFrame':
    """Compute the scaled coefficient covariance inverse for each selected photometer.

    Args:
        input_object (str, pathlib.Path, pandas.DataFrame, list or tuple): Input
            continuous BP/RP mean spectra as a local file, DataFrame, list or
            tuple of integer source IDs, or ADQL query. Formats and reader requirements
            are the same as get_inverse_square_root_covariance_matrix, including
            fields for both photometers when only one is selected.
        band (str or None): 'bp' or 'rp', ignoring case. None computes both
            photometers independently.
        release (str or None): Gaia release. Defaults to 'dr3' when not specified.
            When identifiable, the input release must match the selected release.

    Returns:
        pandas.DataFrame, numpy.ndarray or None: For one source and one selected
        photometer, return its square inverse covariance matrix directly or
        None if no inverse Cholesky factor could be computed. Otherwise, return source_id
        and bp_inverse_covariance and/or rp_inverse_covariance columns, with
        a matrix or None in each cell. Rows follow the prepared input order.

    Raises:
        InvalidBandError: A supplied band is unsupported.
        InvalidReleaseError: A supplied release is unsupported.
        ValueError: Input fields or release information are missing or inconsistent.
    """
    release = parse_release(release)
    band = band if band is None else parse_band(band)
    parsed_input_data, extension, release = InputReader(input_object, get_inverse_covariance_matrix, truncation=False,
                                                        release=release).read()
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
        _lower_inv_iterable = map(_get_inverse_square_root_covariance_matrix_aux, xp_errors, xp_correlation_matrix)
        band_output = map(__get_dot_product, _lower_inv_iterable)
        bands_output.append(band_output)
    output_df = __output_list_to_df(parsed_input_data, bands_output, output_columns)
    if len(bands_to_process) == 1 and len(output_df) == 1:
        return output_df[f'{band}_inverse_covariance'].iloc[0]
    else:
        return output_df


def get_chi2(_lower_inv: np.ndarray, residuals: np.ndarray) -> float:
    """Compute chi-squared using an inverse Cholesky factor and coefficient residuals.

    Args:
        _lower_inv (numpy.ndarray): Inverse lower Cholesky factor W, such as the
            result of get_inverse_square_root_covariance_matrix for one source
            and photometer. Supply the matrix itself, not its containing DataFrame.
        residuals (numpy.ndarray): One-dimensional coefficient residual vector,
            observed minus model, in the same coefficient order as the matrix.

    Returns:
        float: dot(W @ residuals, W @ residuals). For a valid real inverse
        Cholesky factor, this is residuals.T @ inv(C) @ residuals for the covariance C
        represented by W. Dimensions can differ between photometers and releases.

    Raises:
        ValueError: Either input is None, the matrix is not square and
            two-dimensional, or residuals is not a matching one-dimensional array.

    Notes:
        Only presence and dimensions are checked. Inputs must already be NumPy
        arrays with suitable real numeric values; this function does not verify
        finite values or that W corresponds to a valid covariance. It does not
        apply additional scaling by standard_deviation.
    """
    if _lower_inv is None or residuals is None:
        raise ValueError('Input parameters cannot be None.')
    if _lower_inv.ndim != 2 or _lower_inv.shape[0] != _lower_inv.shape[1]:
        raise ValueError('Inverse square root covariance matrix must be a square 2D array.')
    if residuals.ndim != 1 or residuals.shape[0] != _lower_inv.shape[0]:
        raise ValueError('Residuals must be a 1D array with the same number of elements as the covariance matrix '
                         'qdimension.')
    x = dot(_lower_inv, residuals)
    return dot(x.T, x)
