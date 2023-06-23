import unittest

import pandas.testing as pdt

from gaiaxpy.cholesky.cholesky import get_inverse_square_root_covariance_matrix
from tests.test_cholesky.cholesky_solutions import inv_sqrt_cov_matrix_sol_with_missing_df,\
    inv_sqrt_cov_matrix_sol_df_no_missing_df
from tests.utils.utils import missing_bp_source_id


class TestCholeskyArchive(unittest.TestCase):
    def test_external_inverse_square_root_covariance_matrix_no_missing_bands_both_bands_list_input(self):
        input_object = [5853498713190525696, 5762406957886626816]
        output_df = get_inverse_square_root_covariance_matrix(input_object)
        pdt.assert_frame_equal(output_df, inv_sqrt_cov_matrix_sol_df_no_missing_df)

    def test_external_inverse_square_root_covariance_matrix_with_missing_bands_list_input(self):
        input_object = [5853498713190525696, missing_bp_source_id, 5762406957886626816]
        output_df = get_inverse_square_root_covariance_matrix(input_object)
        pdt.assert_frame_equal(output_df, inv_sqrt_cov_matrix_sol_with_missing_df)

    # Query input
    def test_external_inverse_square_root_covariance_matrix_no_missing_bands_both_bands_query_input(self):
        input_object = "SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5853498713190525696', " \
                       "'5762406957886626816')"
        output_df = get_inverse_square_root_covariance_matrix(input_object)
        output_df = output_df.sort_values(by=['source_id']).reset_index(drop=True)
        solution_df = inv_sqrt_cov_matrix_sol_df_no_missing_df.sort_values(by=['source_id']).reset_index(drop=True)
        pdt.assert_frame_equal(output_df, solution_df)

    def test_external_inverse_square_root_covariance_matrix_with_missing_bands_query_input(self):
        input_object = "SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816', " \
                       f"'5853498713190525696', {str(missing_bp_source_id)})"
        output_df = get_inverse_square_root_covariance_matrix(input_object)
        output_df = output_df.sort_values(by=['source_id']).reset_index(drop=True)
        solution_df = inv_sqrt_cov_matrix_sol_with_missing_df.sort_values(by=['source_id']).reset_index(drop=True)
        pdt.assert_frame_equal(output_df, solution_df)
