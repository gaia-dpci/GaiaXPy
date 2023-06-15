import unittest
from os.path import join

import pandas as pd
import pandas.testing as pdt

from gaiaxpy.cholesky.cholesky import get_inverse_square_root_covariance_matrix
from gaiaxpy.core.satellite import BANDS
from tests.test_cholesky.test_cholesky import cholesky_path
from tests.utils.utils import parse_matrices, missing_bp_source_id


class TestCholeskyArchive(unittest.TestCase):
    def test_external_inverse_square_root_covariance_matrix_no_missing_bands_both_bands_list_input(self):
        input_object = [5853498713190525696, 5762406957886626816]
        output_df = get_inverse_square_root_covariance_matrix(input_object)
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_no_missing_bands_solution.csv'),
                                  converters=solution_converters)
        pdt.assert_frame_equal(output_df, solution_df)

    def test_external_inverse_square_root_covariance_matrix_with_missing_bands_list_input(self):
        input_object = [5853498713190525696, missing_bp_source_id, 5762406957886626816]
        output_df = get_inverse_square_root_covariance_matrix(input_object)
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_with_missing_band_solution.csv'),
                                  converters=solution_converters)
        pdt.assert_frame_equal(output_df, solution_df)

    # Query input
    def test_external_inverse_square_root_covariance_matrix_no_missing_bands_both_bands_query_input(self):
        input_object = "SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5853498713190525696', " \
                       "'5762406957886626816')"
        output_df = get_inverse_square_root_covariance_matrix(input_object)
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_no_missing_bands_solution.csv'),
                                  converters=solution_converters)
        output_df = output_df.sort_values(by=['source_id']).reset_index(drop=True)
        solution_df = solution_df.sort_values(by=['source_id']).reset_index(drop=True)
        pdt.assert_frame_equal(output_df, solution_df)

    def test_external_inverse_square_root_covariance_matrix_with_missing_bands_query_input(self):
        input_object = "SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816', " \
                       f"'5853498713190525696', {str(missing_bp_source_id)})"
        output_df = get_inverse_square_root_covariance_matrix(input_object)
        solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
        solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
        solution_df = pd.read_csv(join(cholesky_path, 'inv_sqrt_cov_matrix_with_missing_band_solution.csv'),
                                  converters=solution_converters)
        output_df = output_df.sort_values(by=['source_id']).reset_index(drop=True)
        solution_df = solution_df.sort_values(by=['source_id']).reset_index(drop=True)
        pdt.assert_frame_equal(output_df, solution_df)
