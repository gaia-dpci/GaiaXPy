"""
generic_functions.py
====================================
Module to hold some functions used by different subpackages.
"""

import sys
from ast import literal_eval
from os.path import join
from string import capwords

import numpy as np
import pandas as pd
from numpy import ndarray

from gaiaxpy.config.paths import filters_path, config_path
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.core.custom_errors import InvalidBandError
from gaiaxpy.generator.config import get_additional_filters_path
from gaiaxpy.spectrum.utils import _correlation_to_covariance_dr3int5


def _get_built_in_systems() -> list:
    av_sys = open(join(config_path, 'available_systems.txt'), 'r')
    return av_sys.read().splitlines()


def _is_built_in_system(system):
    return system in _get_built_in_systems()


def cast_output(output):
    cast_dict = {'source_id': 'int64', 'solution_id': 'int64'}
    df = output if isinstance(output, pd.DataFrame) else output.data
    for column in df.columns:
        try:
            df[column] = df[column].astype(cast_dict[column])
        except KeyError:
            continue
    return df


def parse_band(band):
    if isinstance(band, str):
        band = band.lower()
    elif isinstance(band, list) and len(band) == 1:
        band = band[0].lower()
    if band in BANDS:
        return band
    else:
        raise InvalidBandError(band)


def str_to_matrix(str_matrix):
    """
    Convert a string of the form ((1,2,3),(4,5,6),(7,8,9)) to a NumPy matrix.
    """
    # Replace nan to None so the string can be evaluated
    str_matrix = str_matrix.replace('nan', 'None')
    evaluated = literal_eval(str_matrix)
    evaluated = np.array(evaluated)
    evaluated = np.where(evaluated is None, np.nan, evaluated)
    return np.array(evaluated)


def str_to_array(str_array):
    if isinstance(str_array, np.ndarray):
        return str_array
    if isinstance(str_array, str) and len(str_array) >= 2 and str_array[0] == '(' and str_array[1] == '(':
        return str_to_matrix(str_array)
    elif isinstance(str_array, str):
        try:
            return np.fromstring(str_array[1:-1], sep=',')
        except Exception:  # np.fromstring may not raise an error but only show a warning depending on the version
            raise ValueError('Input cannot be converted to array.')
    elif isinstance(str_array, float):
        return float('NaN')
    else:
        raise ValueError('Unhandled type.')


def validate_pwl_sampling(sampling):
    # Receives a NumPy array. Validates sampling in pwl.
    min_sampling_value = -10
    max_sampling_value = 70
    if sampling is None:
        raise ValueError("Sampling can't be None.")
    if len(sampling) == 0:
        raise ValueError('Sampling must contain at least one point.')
    # Must be a numpy array
    if type(sampling) != ndarray:
        raise TypeError('Sampling must be a NumPy array.')
    # Array must be sorted in ascending order
    if not np.array_equal(sampling, np.sort(sampling)):
        raise ValueError('Sampling must be in ascending order.')
    min_value = sampling[0]
    max_value = sampling[-1]
    if min_value < min_sampling_value or max_value > max_sampling_value:
        raise ValueError(f'Wrong value for sampling. Sampling accepts an array of values where the minimum value is '
                         f'{min_sampling_value} and the maximum is {max_sampling_value}.')


def validate_wl_sampling(sampling):
    min_value = 330
    max_value = 1050
    # Check sampling
    if sampling is not None:
        if sampling[0] >= sampling[-1]:
            raise ValueError('Sampling should be a non-decreasing array.')
        elif sampling[0] < min_value or sampling[-1] > max_value:
            raise ValueError(f'Wrong value for sampling. Sampling accepts an array of values where the minimum value '
                             f'is {min_value} and the maximum is {max_value}.')


def _warning(message):
    print(f'UserWarning: {message}', file=sys.stderr)


def validate_arguments(default_output_file, given_output_file, save_file):
    if save_file and not isinstance(save_file, bool):
        raise ValueError("Parameter 'save_file' must contain a boolean value.")
    # If the user input a number different to the default value, but didn't set save_file to True
    if default_output_file != given_output_file and not save_file:
        _warning('Argument output_file was given, but save_file is set to False. Set save_file to True to store the '
                 'output of the function.')


def get_spectra_type(spectra):
    """
    Get the spectra type.

    Args:
        spectra (object): A spectrum or a spectra list.

    Returns:
        str: Spectrum type (e.g. AbsoluteSampledSpectrum).
    """
    if isinstance(spectra, list):
        spectrum = spectra[0]
    elif isinstance(spectra, dict):
        spectrum = spectra[list(spectra.keys())[0]]
    else:
        spectrum = spectra
    return spectrum.__class__


def _get_system_label(name):
    """
    Get the label of the photometric system.

    Returns:
        str: A short description of the photometric system.
    """

    def snake_to_pascal(word):
        return capwords(word.replace("_", " ")).replace(" ", "")

    return snake_to_pascal(name) if _is_built_in_system(name) else name


def _get_system_path(is_built_in):
    return filters_path if is_built_in else get_additional_filters_path()


# AVRO files include the values in the diagonal, whereas others don't
def array_to_symmetric_matrix(array, array_size):
    """
    Convert the input 1D array into a 2D matrix. The array is assumed to store only the unique elements of a symmetric
        matrix (i.e. all elements above the diagonal plus the diagonal) in column major order. A full 2D matrix is
        returned symmetric with respect to the diagonal.

    Args:
        array (ndarray): 1D array.
        array_size (int): number of rows/columns in the output matrix.

    Returns:
        array of arrays: a full 2D matrix.

    Raises:
        TypeError: If array is not of type np.ndarray.
    """

    def contains_diagonal(_array_size, _array):
        return not len(_array) == len(np.tril_indices(_array_size - 1)[0])

    # Is NaN size or NaN array
    if pd.isna(array_size) or (isinstance(array, float) and pd.isna(array)):
        return array
    if isinstance(array_size, float):  # If the missing band source is present, floats may be returned when parsing
        array_size = int(array_size)  # TODO: This should raise an error if the decimal part is not .0
    if isinstance(array, np.ndarray):
        n_dim = array.ndim
        if array.size == 0 or n_dim == 2:  # Either empty or already a matrix
            return array
        elif n_dim == 1:
            array_size = int(array_size)
            matrix = np.zeros((array_size, array_size))
            np.fill_diagonal(matrix, 1.0)  # Add values in diagonal
            k = 0 if contains_diagonal(array_size, array) else -1  # Diagonal offset (from Numpy documentation)
            matrix[np.tril_indices(array_size, k=k)] = array
            transpose = matrix.transpose()
            transpose[np.tril_indices(array_size, -1)] = matrix[np.tril_indices(array_size, -1)]
            return transpose
    raise TypeError('Wrong argument types. Must be np.ndarray and integer or float.')


def _extract_systems_from_data(data_columns, photometric_system=None):
    if isinstance(photometric_system, list):
        return [system.get_system_label() for system in photometric_system]
    src = 'source_id'
    columns = list(data_columns.copy())
    if src in columns:
        columns.remove(src)
    if photometric_system:
        photometric_system = photometric_system if isinstance(photometric_system, list) else [photometric_system]
        systems = [system.get_system_label() for system in photometric_system]
    else:
        # Infer photometric_system from the data
        column_list = [column.split('_')[0] for column in columns]
        systems = list(dict.fromkeys(column_list))
    return systems


def correlation_from_covariance(covariance):
    v = np.sqrt(np.diag(covariance))
    outer_v = np.outer(v, v)
    correlation = covariance / outer_v
    correlation[covariance == 0] = 0
    return correlation


def correlation_to_covariance(correlation: np.ndarray, error: np.ndarray, stdev: float) -> np.ndarray:
    """
    Compute the covariance matrix from the correlation values.

    If the input correlation values are a 1D array, the values are assumed to be the lower triangle of a
    symmetric matrix (excluding the diagonal). The array will be internally converted to a full correlation matrix.

    Args:
        correlation (ndarray): A 2D numpy array of shape (n, n) representing the correlation matrix.
            Alternatively, a 1D numpy array of length n*(n-1)/2 representing the lower triangle of a
            symmetric correlation matrix (excluding the diagonal).
        error (ndarray): A 1D numpy array of length n containing the flux errors.
        stdev (float): The scaling factor for the errors.

    Returns:
        ndarray: A 2D numpy array of shape (n, n) representing the covariance matrix.

    Raises:
        ValueError: If the dimensions of input correlation are not either 1 or 2.
    """
    if correlation.ndim == 1:
        size = get_matrix_size_from_lower_triangle(correlation)
        new_matrix = np.zeros((size, size))
        new_matrix[np.tril_indices(size, k=-1)] = correlation
        new_matrix += new_matrix.T
        new_matrix += np.diag(np.ones(size), k=0)
        correlation = new_matrix
    if correlation.ndim == 2:
        return _correlation_to_covariance_dr3int5(correlation, error, stdev)
    else:
        raise ValueError('Dimensions of input correlation must be either 1 or 2.')


def get_matrix_size_from_lower_triangle(array):
    """
    Compute the size of a symmetric matrix from an array containing the values of its lower triangle, excluding the
    diagonal.

    Args:
        array (ndarray): An array of length n*(n-1)/2 representing the lower triangle of an n x n symmetric matrix,
            excluding the diagonal.

    Returns:
        int: The size n of the symmetric matrix.

    Raises:
        ValueError: If the length of array is not a valid input for a symmetric matrix lower triangle.
    """
    return int((np.sqrt(1 + 8 * len(array)) + 1) / 2)


def standardise_extension(_extension):
    """
    Standardise the provided extension which can contain or not an initial dot, and can contain a mix of uppercase and
    lowercase letters.

    Args:
        _extension (str): File extension which may or may not contain an initial dot.

    Returns:
        str: The extension in lowercase letters and with no initial dot (eg.: 'csv').
    """
    # Remove initial dot if present
    _extension = _extension[1:] if _extension[0] == '.' else _extension
    return _extension.lower()
