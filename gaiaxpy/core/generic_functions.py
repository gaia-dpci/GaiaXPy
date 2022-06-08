"""
generic_functions.py
====================================
Module to hold some functions used by different subpackages.
"""

import sys
import numpy as np
from collections.abc import Iterable
from numbers import Number
from numpy import ndarray
from string import capwords


def _validate_pwl_sampling(sampling):
    # Receives a numpy array. Validates sampling in pwl.
    min_sampling_value = -10
    max_sampling_value = 70
    if sampling is None:
        raise ValueError("Sampling can't be None.")
    if len(sampling) == 0:
        raise ValueError('Sampling must contain at least one point.')
    # Must be a numpy array
    if type(sampling) != ndarray:
        raise TypeError('Sampling must be a NumPy array.')
    # Array must be sorted in ascendent order
    sorted_sampling = np.sort(sampling)
    if not np.array_equal(sampling, sorted_sampling):
        raise ValueError('Sampling must be in ascendent order.')
    min_value = sampling[0]
    max_value = sampling[-1]
    if min_value < min_sampling_value or max_value > max_sampling_value:
        raise ValueError(f'Wrong value for sampling. Sampling accepts an array of values where the minimum value is {min_sampling_value} and the maximum is {max_sampling_value}.')


def _validate_wl_sampling(sampling):
    min_value = 330
    max_value = 1050
    # Check sampling
    if sampling is not None:
        if sampling[0] >= sampling[-1]:
            raise ValueError('Sampling should be a non-decreasing array.')
        elif sampling[0] < min_value or sampling[-1] > max_value:
            raise ValueError(f'Wrong value for sampling. Sampling accepts an array of values where the minimum value is {min_value} and the maximum is {max_value}.')


def _warning(message):
    print(f'UserWarning: {message}', file=sys.stderr)


def _validate_arguments(default_output_file, given_output_file, save_file):
    if save_file and not isinstance(save_file, bool):
        raise ValueError("Parameter 'save_file' must contain a boolean value.")
    # If the user gave a number different than the default value, but didn't set save_file to True
    if default_output_file != given_output_file and save_file == False:
        _warning('Argument output_file was given, but save_file is set to False. Set save_file to True to store the output of the function.')


def _progress_tracker(func):
    # Progress tracker decorator
    def inner(row, *args):
        if args:
            index = args[-2]
            nrows = args[-1]
            print('Processing data [{:.0%}]\r'.format((index + 1) / nrows), end="")
            func(row, *args[:-2])
            print(' ' * 30 + '\r', end='')
    return inner


def _get_spectra_type(spectra):
    """
    Get the spectra type.

    Args:
        spectra (object): A spectrum or a spectra iterable.

    Returns:
        str: Spectrum type (e.g. AbsoluteSampledSpectrum).
    """
    if isinstance(spectra, Iterable):
        spectrum = spectra[0]
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
    return snake_to_pascal(name)


# AVRO files include the values in the diagonal, whereas others don't
def array_to_symmetric_matrix(size, array):
    """
    Convert the input 1D array into a 2D matrix. The array is assumed to store
    only the unique elements of a symmetric matrix (i.e. all elements
    above the diagonal plus the diagonal) in column major order. A full 2D matrix
    is returned symmetric with respect to the diagonal.

    Args:
        size (int): number of rows/columns in the output matrix.
        array (ndarray): 1D array.

    Returns:
        array of arrays: a full 2D matrix.

    Raises:
        TypeError: If array is not of type np.ndarray.
    """
    def contains_diagonal(size, array):
        if len(array) == len(np.tril_indices(size - 1)[0]):
            return False
        return True
    # Enforce array type, second check verifies that array is 1D.
    if isinstance(array, np.ndarray) and isinstance(array[0], Number) and isinstance(size, Number):
        k = -1  # Diagonal offset (from Numpy documentation)
        matrix = np.zeros((size, size))
        # Add values in diagonal
        np.fill_diagonal(matrix, 1.0)
        if contains_diagonal(size, array):
            k = 0
        matrix[np.tril_indices(size, k=k)] = array
        transpose = matrix.transpose()
        transpose[np.tril_indices(
            size, -1)] = matrix[np.tril_indices(size, -1)]
        return transpose
    elif isinstance(array[0], np.ndarray):
        # Input array is already a matrix, we assume that it contains the required values.
        return array
    else:
        raise TypeError('Wrong argument types. Must be integer and np.ndarray.')


def _extract_systems_from_data(data_columns, photometric_system):
    src = 'source_id'
    columns = list(data_columns.copy())
    if src in columns:
        columns.remove(src)
    if photometric_system is None:
        # Infer photometric_system from the data
        column_list = [column.split('_')[0] for column in columns]
        systems = list(dict.fromkeys(column_list))
    else:
        if not isinstance(photometric_system, list):
            photometric_system = [photometric_system]
        systems = [system.get_system_label() for system in photometric_system]
    return systems
