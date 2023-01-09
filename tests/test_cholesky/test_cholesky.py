import unittest
from os.path import join

import numpy as np
import numpy.testing as npt
import pandas as pd

from gaiaxpy import get_chi2, get_inverse_covariance_matrix
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import files_path

cholesky_path = join(files_path, 'cholesky_solution')
f = join(cholesky_path, '18Sco-XP-spectra.csv')
# Load solution (only BP solution is available from the notebook)
solution = np.loadtxt(join(cholesky_path, 'nb_bp_get_inv_cov_mat.txt'))


class TestCholesky(unittest.TestCase):

    def test_inverse_covariance_matrix_from_file(self):
        inverse_df = get_inverse_covariance_matrix(f)
        inverse_cov = inverse_df['bp_inverse_covariance'].iloc[0]
        npt.assert_array_almost_equal(inverse_cov, solution)

    def test_inverse_covariance_matrix_from_df_str(self):
        df = pd.read_csv(f)
        inverse_df = get_inverse_covariance_matrix(df)
        inverse_cov = inverse_df['bp_inverse_covariance'].iloc[0]
        npt.assert_array_almost_equal(inverse_cov, solution)

    def test_inverse_covariance_matrix_file_from_df_numpy_array(self):
        df = pd.read_csv(f)
        # Correlations and error should be numpy array
        df['bp_coefficient_correlations'] = df['bp_coefficient_correlations'].map(str_to_array)
        df['bp_coefficient_errors'] = df['bp_coefficient_errors'].map(str_to_array)
        inverse_df = get_inverse_covariance_matrix(df)
        inverse_cov = inverse_df['bp_inverse_covariance'].iloc[0]
        npt.assert_array_almost_equal(inverse_cov, solution)

    def test_inverse_covariance_matrix_file_from_df_numpy_matrix(self):
        # Test completely parsed (arrays + matrices) dataframe
        df, _ = InputReader(f, get_inverse_covariance_matrix)._read()
        inverse_df = get_inverse_covariance_matrix(df)
        inverse_cov = inverse_df['bp_inverse_covariance'].iloc[0]
        npt.assert_array_almost_equal(inverse_cov, solution)

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