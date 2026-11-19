import numpy as np
import pandas as pd
import pytest

from gaiaxpy.core.generic_functions import array_to_symmetric_matrix
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.dataframe_reader import DataFrameReader
from gaiaxpy.input_reader.file_reader import FileReader, FileParserSelector

# Upper triangle by columns: (0, 1), (0, 2), (1, 2),
#                           (0, 3), (1, 3), (2, 3).
PACKED_CORRELATIONS = np.array([0.01, 0.02, 0.03, 0.04, 0.05, 0.06])
FULL_CORRELATIONS = np.array([
    [1.00, 0.01, 0.02, 0.04],
    [0.01, 1.00, 0.03, 0.05],
    [0.02, 0.03, 1.00, 0.06],
    [0.04, 0.05, 0.06, 1.00]
])


def test_packed_correlations_use_upper_triangle_column_major_order():
    original = PACKED_CORRELATIONS.copy()
    assert original.size == 4 * (4 - 1) // 2
    result = array_to_symmetric_matrix(original, 4)
    np.testing.assert_array_equal(result, FULL_CORRELATIONS)
    np.testing.assert_array_equal(np.diag(result), [1., 1., 1., 1.])
    np.testing.assert_array_equal(result, result.T)
    np.testing.assert_array_equal(original, PACKED_CORRELATIONS)


def test_full_matrix_is_returned_unchanged():
    # Distinct diagonal values catch accidental replacement with ones.
    matrix = FULL_CORRELATIONS.copy()
    np.fill_diagonal(matrix, [2., 3., 4., 5.])
    expected = matrix.copy()
    result = array_to_symmetric_matrix(matrix, 4)
    assert result is matrix
    np.testing.assert_array_equal(result, expected)


def test_covariance_array_includes_its_diagonal_in_column_major_order():
    packed = np.array([2., 0.01, 3., 0.02, 0.03, 4., 0.04, 0.05, 0.06, 5.])
    expected = FULL_CORRELATIONS.copy()
    np.fill_diagonal(expected, [2., 3., 4., 5.])
    np.testing.assert_array_equal(array_to_symmetric_matrix(packed, 4), expected)


def _mean_spectrum(correlations):
    # Four parameters keep every expected matrix element explicit in these
    # reader tests; no calibration or release identification is performed.
    data = {'source_id': [42]}
    for band in BANDS:
        data.update({
            f'{band}_n_parameters': [4],
            f'{band}_coefficients': [np.array([10., 20., 30., 40.])],
            f'{band}_standard_deviation': [1.],
            f'{band}_coefficient_errors': [np.array([1., 2., 3., 4.])],
            f'{band}_coefficient_correlations': [correlations.copy()]
        })
    return pd.DataFrame(data)


def _array_as_string(array):
    # Nested tuples are the supported string representation of full matrices.
    if array.ndim == 2:
        return repr(tuple(tuple(float(value) for value in row) for row in array))
    return repr(tuple(float(value) for value in array))


@pytest.mark.parametrize('function', ['calibrate', 'convert', 'generate'])
@pytest.mark.parametrize('representation', ['packed', 'full'])
@pytest.mark.parametrize('input_type', ['dataframe', 'csv'])
def test_readers_reconstruct_packed_correlations_and_preserve_full_matrices(
        tmp_path, function, representation, input_type):
    correlations = PACKED_CORRELATIONS if representation == 'packed' else FULL_CORRELATIONS
    data = _mean_spectrum(correlations)
    if input_type == 'dataframe':
        reader = DataFrameReader(data, function, truncation=False, disable_info=True)
    else:
        serialised = data.copy()
        for column in serialised.columns:
            if column.endswith(('_coefficients', '_coefficient_errors', '_coefficient_correlations')):
                serialised[column] = serialised[column].map(_array_as_string)
        path = tmp_path / 'spectra.csv'
        serialised.to_csv(path, index=False)
        reader = FileReader(FileParserSelector(function), path, truncation=False, disable_info=True)

    parsed, _ = reader.read()
    for band in BANDS:
        column = f'{band}_coefficient_correlations'
        np.testing.assert_array_equal(parsed[column].iloc[0], FULL_CORRELATIONS)
        np.testing.assert_array_equal(data[column].iloc[0], correlations)
        np.testing.assert_array_equal(parsed[f'{band}_coefficients'].iloc[0], [10., 20., 30., 40.])
        np.testing.assert_array_equal(parsed[f'{band}_coefficient_errors'].iloc[0], [1., 2., 3., 4.])
