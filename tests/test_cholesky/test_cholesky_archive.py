import pandas.testing as pdt
import pytest

from gaiaxpy.cholesky.cholesky import get_inverse_square_root_covariance_matrix
from tests.test_cholesky.cholesky_solutions import (inv_sqrt_cov_matrix_sol_with_missing_df,
                                                    inv_sqrt_cov_matrix_sol_no_missing_df)
from tests.utils.utils import missing_bp_source_id


@pytest.mark.archive
@pytest.mark.parametrize('input_data,solution', [([5853498713190525696, 5762406957886626816],
                                                  inv_sqrt_cov_matrix_sol_no_missing_df),
                                                 ("SELECT * FROM gaiadr3.gaia_source WHERE source_id IN"
                                                  " ('5853498713190525696', '5762406957886626816')",
                                                  inv_sqrt_cov_matrix_sol_no_missing_df),
                                                 ([5853498713190525696, missing_bp_source_id, 5762406957886626816],
                                                  inv_sqrt_cov_matrix_sol_with_missing_df),
                                                 ("SELECT * FROM gaiadr3.gaia_source WHERE source_id IN "
                                                  "('5762406957886626816', '5853498713190525696', "
                                                  f"{str(missing_bp_source_id)})",
                                                  inv_sqrt_cov_matrix_sol_with_missing_df)])
def test_external_inverse_square_root_covariance_matrix(input_data, solution):
    output_df = get_inverse_square_root_covariance_matrix(input_data)
    output_df = output_df.sort_values(by=['source_id']).reset_index(drop=True)
    solution_df = solution.sort_values(by=['source_id']).reset_index(drop=True)
    pdt.assert_frame_equal(output_df, solution_df)
