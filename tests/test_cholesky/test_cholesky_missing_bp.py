import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt
import unittest
from gaiaxpy import get_chi2, get_inverse_covariance_matrix
from gaiaxpy.cholesky.cholesky import get_inverse_square_root_covariance_matrix
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.core.satellite import BANDS
from os.path import join
from tests.files.paths import files_path
from tests.utils.utils import parse_matrices

input_path = join(files_path, 'xp_continuous')
input_file = join(input_path, 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
input_array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficients',
                       'rp_coefficient_errors', 'rp_coefficient_correlations']
input_converters = dict([(column, lambda x: str_to_array(x)) for column in input_array_columns])

solution_path = join(files_path, 'cholesky_solution')
solution_file = join(solution_path, 'get_inv_cov_with_missing_bp.csv')
solution_array_columns = [f'{band}_inverse_covariance' for band in BANDS]
solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
solution_df = pd.read_csv(solution_file, converters=solution_converters)

missing_bp_source_id = 5405570973190252288


class TestCholeskyMissingBP(unittest.TestCase):

    def test_covariance_missing_bp(self):
        output_df = get_inverse_covariance_matrix(input_file)
        pdt.assert_frame_equal(output_df, solution_df)

    def test_covariance_missing_bp_isolated_source(self):
        df = pd.read_csv(input_file, converters=input_converters)
        df = df[df['source_id'] == missing_bp_source_id]
        output_df = get_inverse_covariance_matrix(df)
        filtered_solution_df = solution_df[solution_df['source_id'] == missing_bp_source_id].reset_index(drop=True)
        pdt.assert_frame_equal(output_df, filtered_solution_df)

    def test_covariance_missing_bp_isolated_source_bp(self):
        band = 'bp'
        df = pd.read_csv(input_file, converters=input_converters)
        df = df[df['source_id'] == missing_bp_source_id]
        output = get_inverse_covariance_matrix(df, band=band)
        solution = solution_df[solution_df['source_id'] == missing_bp_source_id].iloc[0][f'{band}_inverse_covariance']
        npt.assert_array_equal(output, solution)

    def test_covariance_missing_bp_isolated_source_rp(self):
        band = 'rp'
        df = pd.read_csv(input_file, converters=input_converters)
        df = df[df['source_id'] == missing_bp_source_id]
        output = get_inverse_covariance_matrix(df, band=band)
        solution = solution_df[solution_df['source_id'] == missing_bp_source_id].iloc[0][f'{band}_inverse_covariance']
        npt.assert_array_almost_equal(output, solution)

    def test_get_chi2_values_missing_source_error(self):
        f = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
        inv_sqrt_cov_df = get_inverse_square_root_covariance_matrix(f)
        inv_sqrt_cov_row = inv_sqrt_cov_df[inv_sqrt_cov_df['source_id'] == missing_bp_source_id].iloc[0]
        bp_inv_sqrt_cov = inv_sqrt_cov_row['bp_inverse_square_root_covariance_matrix']
        rp_inv_sqrt_cov = inv_sqrt_cov_row['rp_inverse_square_root_covariance_matrix']
        mock_residuals = np.array(list(range(55)))
        with self.assertRaises(ValueError):
            get_chi2(bp_inv_sqrt_cov, mock_residuals)
        self.assertAlmostEqual(get_chi2(rp_inv_sqrt_cov, mock_residuals), 4047255.681776895, places=7)
