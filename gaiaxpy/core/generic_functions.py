"""
generic_functions.py
====================================
Module to hold some functions used by different subpackages.
"""

import sys
from collections.abc import Iterable
from numbers import Number
from os.path import join
from string import capwords
from os.path import join
from gaiaxpy.config.paths import config_path

import numpy as np
import pandas as pd
from numpy import ndarray

from gaiaxpy.config.paths import filters_path, config_path
from gaiaxpy.generator.config import get_additional_filters_path


def _get_built_in_systems() -> list:
    f = open(join(config_path, 'available_systems.txt'), 'r')
    built_in_systems = f.read().splitlines()
    return built_in_systems


def _is_built_in_system(system):
    return system in _get_built_in_systems()


def cast_output(output):
    cast_dict = {'source_id': 'int64', 'solution_id': 'int64'}
    df = output if isinstance(output, pd.DataFrame) else output.data
    for key, value in cast_dict.items():
        try:
            df[key] = df[key].astype(value)
        except KeyError:
            continue
    return df


def str_to_array(str_array):
    if isinstance(str_array, str):
        try:
            return np.fromstring(str_array[1:-1], sep=',')
        except:
            raise ValueError('Input cannot be converted to array.')
    elif isinstance(str_array, float):
        return float('NaN')
    else:
        raise ValueError('Unhandled type.')


def _validate_pwl_sampling(sampling):
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


def _validate_wl_sampling(sampling):
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


def _validate_arguments(default_output_file, given_output_file, save_file):
    if save_file and not isinstance(save_file, bool):
        raise ValueError("Parameter 'save_file' must contain a boolean value.")
    # If the user input a number different to the default value, but didn't set save_file to True
    if default_output_file != given_output_file and not save_file:
        _warning('Argument output_file was given, but save_file is set to False. Set save_file to True to store the '
                 'output of the function.')


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

    # Bad cases
    if (not isinstance(array, np.ndarray) and np.isnan(array)) or isinstance(array_size, np.ma.core.MaskedConstant) \
            or array.size == 0:
        return array
    # Enforce array type, second check verifies that array is 1D.
    if isinstance(array, np.ndarray) and isinstance(array[0], Number) and isinstance(array_size, Number):
        array_size = int(array_size)
        matrix = np.zeros((array_size, array_size))
        np.fill_diagonal(matrix, 1.0)  # Add values in diagonal
        k = 0 if contains_diagonal(array_size, array) else -1  # Diagonal offset (from Numpy documentation)
        matrix[np.tril_indices(array_size, k=k)] = array
        transpose = matrix.transpose()
        transpose[np.tril_indices(array_size, -1)] = matrix[np.tril_indices(array_size, -1)]
        return transpose
    elif isinstance(array, np.ndarray) and isinstance(array[0], np.ndarray):
        # Input array is already a matrix, we assume that it contains the required values.
        return array
    else:
        raise TypeError('Wrong argument types. Must be np.ndarray and integer.')


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

def _get_built_in_systems() -> list:
    f = open(join(config_path, 'available_systems.txt'), 'r')
    return f.read().splitlines()
