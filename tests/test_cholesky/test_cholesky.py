import unittest
from os.path import join

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import get_chi2, get_inverse_covariance_matrix
from gaiaxpy.cholesky.cholesky import _get_inverse_square_root_covariance_matrix_aux, \
    get_inverse_square_root_covariance_matrix
from gaiaxpy.core.generic_functions import str_to_array, array_to_symmetric_matrix
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import files_path
from tests.utils.utils import parse_matrices

cholesky_path = join(files_path, 'cholesky_solution')
# Load solution (only BP solution is available from the notebook)
matrix_columns = ['bp_inverse_covariance', 'rp_inverse_covariance']
converters = dict([(column, lambda x: parse_matrices(x)) for column in matrix_columns])
solution = pd.read_csv(join(cholesky_path, 'test_cholesky_solution.csv'), float_precision='high', converters=converters)

_rtol = 1e-05
_atol = 1e-05


class TestCholesky(unittest.TestCase):

    def test_inverse_covariance_matrix_from_file(self):
        f = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.xml')
        inverse_df = get_inverse_covariance_matrix(f)
        pdt.assert_frame_equal(inverse_df, solution, rtol=_rtol, atol=_atol)

    def test_inverse_covariance_matrix_from_df_str(self):
        f = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
        df = pd.read_csv(f)
        inverse_df = get_inverse_covariance_matrix(df)
        pdt.assert_frame_equal(inverse_df, solution, rtol=_rtol, atol=_atol)

    def test_inverse_covariance_matrix_file_from_df_numpy_array(self):
        f = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
        df = pd.read_csv(f)
        # Correlations and error should be NumPy array
        for column in ['bp_coefficient_correlations', 'bp_coefficient_errors', 'rp_coefficient_correlations',
                       'rp_coefficient_errors']:
            df[column] = df[column].map(str_to_array)
        for column in ['bp_coefficient_correlations', 'rp_coefficient_correlations']:
            df[column] = df[column].apply(lambda row: array_to_symmetric_matrix(row, 55))
        inverse_df = get_inverse_covariance_matrix(df)
        pdt.assert_frame_equal(inverse_df, solution, rtol=_rtol, atol=_atol)

    def test_inverse_covariance_matrix_file_from_df_numpy_matrix(self):
        # Test completely parsed (arrays + matrices) dataframe
        f = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
        df, _ = InputReader(f, get_inverse_covariance_matrix).read()
        inverse_df = get_inverse_covariance_matrix(df)
        pdt.assert_frame_equal(inverse_df, solution, rtol=_rtol, atol=_atol)

    def test_get_chi2(self):
        matrix = np.random.rand(55, 55)
        residuals = np.random.rand(55)
        output = get_chi2(matrix, residuals)
        self.assertIsInstance(output, float)

    def test_get_chi2_wrong_length(self):
        matrix = np.random.rand(55, 55)
        residuals = np.random.rand(54)
        with self.assertRaises(ValueError):
            output = get_chi2(matrix, residuals)

    def test_get_chi2_values(self):
        f = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW.csv')
        inv_sqrt_cov_df = get_inverse_square_root_covariance_matrix(f)
        inv_sqrt_cov_row = inv_sqrt_cov_df[inv_sqrt_cov_df['source_id'] == 5853498713190525696].iloc[0]
        bp_inv_sqrt_cov = inv_sqrt_cov_row['bp_inverse_square_root_covariance_matrix']
        mock_residuals = np.array(list(range(55)))
        self.assertAlmostEqual(get_chi2(bp_inv_sqrt_cov, mock_residuals), 16655.037182417516, places=7)


class TestInverseSquareRootCovarianceMatrix(unittest.TestCase):

    def test_internal_inverse_square_root_covariance_matrix_no_missing_bands(self):
        input_object = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW.csv')
        parsed_input_data, extension = InputReader(input_object, get_inverse_square_root_covariance_matrix).read()
        output_columns = ['source_id', 'bp_inverse_square_root_covariance_matrix',
                          'rp_inverse_square_root_covariance_matrix']
        bands_output = []
        for b in BANDS:
            xp_errors = (parsed_input_data[f'{b}_coefficient_errors'] / parsed_input_data[f'{b}_standard_deviation'])
            xp_correlation_matrix = parsed_input_data[f'{b}_coefficient_correlations']
            band_output = map(_get_inverse_square_root_covariance_matrix_aux, xp_errors, xp_correlation_matrix)
            bands_output.append(band_output)
        output_list = [parsed_input_data['source_id']]
        for element in bands_output:
            output_list.append(element)
        output_df = pd.DataFrame(zip(*output_list), columns=output_columns)
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_no_missing_bands_solution.csv'),
                                  converters=solution_converters)
        pdt.assert_frame_equal(output_df, solution_df)

    def test_internal_inverse_square_root_covariance_matrix_with_missing_bands(self):
        input_object = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
        parsed_input_data, extension = InputReader(input_object, get_inverse_square_root_covariance_matrix).read()
        output_columns = ['source_id', 'bp_inverse_square_root_covariance_matrix',
                          'rp_inverse_square_root_covariance_matrix']
        bands_output = []
        for b in BANDS:
            xp_errors = (parsed_input_data[f'{b}_coefficient_errors'] / parsed_input_data[f'{b}_standard_deviation'])
            xp_correlation_matrix = parsed_input_data[f'{b}_coefficient_correlations']
            band_output = map(_get_inverse_square_root_covariance_matrix_aux, xp_errors, xp_correlation_matrix)
            bands_output.append(band_output)
        output_list = [parsed_input_data['source_id']]
        for element in bands_output:
            output_list.append(element)
        output_df = pd.DataFrame(zip(*output_list), columns=output_columns)
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_with_missing_band_solution.csv'),
                                  converters=solution_converters)
        pdt.assert_frame_equal(output_df, solution_df)

    # File input

    def test_external_inverse_square_root_covariance_matrix_no_missing_bands_both_bands_file_input(self):
        input_object = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW.csv')
        output_df = get_inverse_square_root_covariance_matrix(input_object)
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_no_missing_bands_solution.csv'),
                                  converters=solution_converters)
        pdt.assert_frame_equal(output_df, solution_df)

    def test_external_inverse_square_root_covariance_matrix_with_missing_bands_file_input(self):
        input_object = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
        output_df = get_inverse_square_root_covariance_matrix(input_object)
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_with_missing_band_solution.csv'),
                                  converters=solution_converters)
        pdt.assert_frame_equal(output_df, solution_df)

    # DF input
    def test_external_inverse_square_root_covariance_matrix_no_missing_bands_both_bands_df_input(self):
        input_object = pd.read_csv(join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW.csv'))
        output_df = get_inverse_square_root_covariance_matrix(input_object)
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_no_missing_bands_solution.csv'),
                                  converters=solution_converters)
        pdt.assert_frame_equal(output_df, solution_df)

    def test_external_inverse_square_root_covariance_matrix_with_missing_bands_df_input(self):
        input_object = pd.read_csv(join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv'))
        output_df = get_inverse_square_root_covariance_matrix(input_object)
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_with_missing_band_solution.csv'),
                                  converters=solution_converters)
        pdt.assert_frame_equal(output_df, solution_df)

    # Single band tests
    def test_external_inverse_square_root_covariance_matrix_no_missing_bands_bp_file_input(self):
        input_object = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW.csv')
        output_df = get_inverse_square_root_covariance_matrix(input_object, band='BP')
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_no_missing_bands_solution.csv'),
                                  converters=solution_converters)
        output_columns = output_df.columns
        pdt.assert_frame_equal(output_df, solution_df[output_columns])

    def test_external_inverse_square_root_covariance_matrix_with_missing_bands_rp_file_input(self):
        input_object = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.ecsv')
        output_df = get_inverse_square_root_covariance_matrix(input_object, band=['rP'])
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_with_missing_band_solution.csv'),
                                  converters=solution_converters)
        output_columns = output_df.columns
        pdt.assert_frame_equal(output_df, solution_df[output_columns])

    # One source ID
    def test_external_inverse_square_root_covariance_matrix_one_row_one_band_input(self):
        f = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
        input_object = pd.read_csv(f).iloc[[2]]  # Select just one row
        output = get_inverse_square_root_covariance_matrix(input_object, band='rP')
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_with_missing_band_solution.csv'),
                                  converters=solution_converters)
        # Almost equal as the solution file contains fewer decimals than the ones returned by the function
        npt.assert_array_almost_equal(output, solution_df['rp_inverse_square_root_covariance_matrix'].iloc[2])
