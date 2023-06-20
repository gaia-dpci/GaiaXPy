import unittest

import numpy as np
import numpy.testing as npt
import pandas.testing as pdt

from gaiaxpy import get_chi2, get_inverse_covariance_matrix
from gaiaxpy.cholesky.cholesky import get_inverse_square_root_covariance_matrix
from tests.files.paths import with_missing_bp_csv_file
from tests.test_cholesky.cholesky_paths import inv_cov_with_missing_df, isolated_missing_df
from tests.utils.utils import missing_bp_source_id


class TestCholeskyMissingBP(unittest.TestCase):

    def test_covariance_missing_bp(self):
        output_df = get_inverse_covariance_matrix(with_missing_bp_csv_file)
        pdt.assert_frame_equal(output_df, inv_cov_with_missing_df)

    def test_covariance_missing_bp_isolated_source(self):
        output_df = get_inverse_covariance_matrix(isolated_missing_df)
        filtered_solution_df = inv_cov_with_missing_df[inv_cov_with_missing_df['source_id'] ==
                                                       missing_bp_source_id].reset_index(drop=True)
        pdt.assert_frame_equal(output_df, filtered_solution_df)

    def test_covariance_missing_bp_isolated_source_bp(self):
        band = 'bp'
        output = get_inverse_covariance_matrix(isolated_missing_df, band=band)
        solution = inv_cov_with_missing_df[inv_cov_with_missing_df['source_id'] ==
                                           missing_bp_source_id].iloc[0][f'{band}_inverse_covariance']
        npt.assert_array_equal(output, solution)

    def test_covariance_missing_bp_isolated_source_rp(self):
        band = 'rp'
        output = get_inverse_covariance_matrix(isolated_missing_df, band=band)
        solution = inv_cov_with_missing_df[inv_cov_with_missing_df['source_id'] ==
                                           missing_bp_source_id].iloc[0][f'{band}_inverse_covariance']
        npt.assert_array_almost_equal(output, solution)

    def test_get_chi2_values_missing_source_error(self):
        inv_sqrt_cov_df = get_inverse_square_root_covariance_matrix(with_missing_bp_csv_file)
        inv_sqrt_cov_row = inv_sqrt_cov_df[inv_sqrt_cov_df['source_id'] == missing_bp_source_id].iloc[0]
        bp_inv_sqrt_cov = inv_sqrt_cov_row['bp_inverse_square_root_covariance_matrix']
        rp_inv_sqrt_cov = inv_sqrt_cov_row['rp_inverse_square_root_covariance_matrix']
        mock_residuals = np.array(list(range(55)))
        with self.assertRaises(ValueError):
            get_chi2(bp_inv_sqrt_cov, mock_residuals)
        self.assertAlmostEqual(get_chi2(rp_inv_sqrt_cov, mock_residuals), 4047255.681776895, places=7)
