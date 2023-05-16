import json
from numbers import Number
import numpy as np
import pandas as pd
import pytest
from gaiaxpy.core.generic_functions import str_to_array, array_to_symmetric_matrix


def array_to_symmetric_matrix_row_major(size, array):
    """
    Convert the input 1D array into a 2D matrix. Contrary to what is normally done for BP/RP spectra covariance and
    correlation matrices, this method works on the assumption that the upper triangular matrix has been written in row
    major order.
    A full 2D matrix is returned symmetric with respect to the diagonal.

    Args:
        size (int): number of rows/columns in the output matrix.
        array (ndarray): 1D array.

    Returns:
        ndarray: a full 2D matrix.

    Raises:
        TypeError: If array is not of type np.ndarray.
    """
    # Enforce array type, second check verifies that array is 1D.
    if isinstance(array, np.ndarray) and isinstance(array[0], Number) and isinstance(size, (int, np.int64)):
        matrix = np.zeros((size, size))
        matrix[np.triu_indices(size)] = array
        transpose = matrix.transpose()
        transpose[np.triu_indices(size)] = matrix[np.triu_indices(size)]
        return transpose
    elif isinstance(array[0], np.ndarray):
        return array  # Input array is already a matrix, we assume that it contains the required values.
    else:
        raise TypeError('Wrong argument types. Must be integer and np.ndarray.')

_rtol, _atol = 1e-7, 1e-7


def parse_matrices(string):
    return None if len(string) == 0 else np.array(json.loads(string))


def get_spectrum_with_source_id(source_id, spectra):
    if isinstance(spectra, list):
        for spectrum in spectra:
            if spectrum.get_source_id() == source_id:
                return spectrum
    elif isinstance(spectra, pd.DataFrame):
        return spectra.loc[spectra['source_id'] == source_id].to_dict('records')[0]
    raise ValueError('Spectrum does not exist or function is not defined for variable spectra type.')


def get_spectrum_with_source_id_and_xp(source_id, xp, spectra):
    if isinstance(spectra, list):
        for spectrum in spectra:
            if spectrum.get_source_id() == source_id and spectrum.get_xp() == xp:
                return spectrum
    elif isinstance(spectra, pd.DataFrame):
        return spectra.loc[(spectra['source_id'] == source_id) & (spectra['xp'] == xp.upper())].to_dict('records')[0]
    raise ValueError('Spectrum does not exist or function is not defined for variable spectra type.')


def pos_file_to_array(pos_file):
    df = pd.read_csv(pos_file, float_precision='round_trip', converters={'pos': (lambda x: str_to_array(x))})
    return df['pos'].iloc[0]


# Define the converter function
def str_to_array_rec(input_str, dtypes):
    lst = eval(input_str)
    lst = [tuple(element) for element in lst]
    output = [np.array(line, dtype=dtypes) for line in lst]
    return np.array(output)


def get_converters(columns, dtypes=None):
    if isinstance(columns, str):
        return {columns: lambda x: str_to_array_rec(x, dtypes)}
    elif isinstance(columns, list):
        if len(columns) == 1:
            return {columns[0]: lambda x: str_to_array_rec(x, dtypes)}
        elif len(columns) > 1:  # Extrema BP and RP case
            return {column: lambda x: str_to_array(x) for column in columns}
    raise ValueError("Input doesn't correspond to any of the expected types.")

    
def df_columns_to_array(df, columns):
    for index, row in df.iterrows():
        for column in columns:
            df[column][index] = str_to_array(row[column])
    return df


def reconstruct_covariance(array):
    def get_matrix_size(d):
        num_elements = len(d)
        return int((-1 + np.sqrt(1 + 8 * num_elements)) / 2)
    size = get_matrix_size(array)
    return array_to_symmetric_matrix(array, size)
