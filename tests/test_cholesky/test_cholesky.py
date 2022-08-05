import unittest
import numpy as np
import numpy.testing as npt
import pandas as pd
from os.path import join
from gaiaxpy.cholesky.cholesky import get_chi2, get_inverse_covariance_matrix
from gaiaxpy.core.generic_functions import array_to_symmetric_matrix
from tests.files import files_path


f = join(files_path, 'cholesky', '18Sco-XP-spectra.csv')
# Load solution (only BP solution is available)
solution = np.loadtxt(join(files_path, 'cholesky', 'nb_bp_get_inv_cov_mat.txt'))


def str_to_np_array(array):
    return np.fromstring(array[1:-1], sep=',')


class TestCholesky(unittest.TestCase):

    def test_inverse_covariance_matrix_from_file(self):
        inverse = get_inverse_covariance_matrix(f, band='bp')
        npt.assert_array_almost_equal(inverse, solution)

    def test_inverse_covariance_matrix_from_df_str(self):
        df = pd.read_csv(f)
        inverse = get_inverse_covariance_matrix(df, band='bp')
        npt.assert_array_almost_equal(inverse, solution)

    def test_inverse_covariance_matrix_file_from_df_numpy_array(self):
        df = pd.read_csv(f)
        # Correlations and error should be numpy array
        df['bp_coefficient_correlations'] = df['bp_coefficient_correlations'].map(str_to_np_array)
        df['bp_coefficient_errors'] = df['bp_coefficient_errors'].map(str_to_np_array)
        inverse = get_inverse_covariance_matrix(df, band='bp')
        npt.assert_array_almost_equal(inverse, solution)

    def test_inverse_covariance_matrix_file_from_df_numpy_matrix(self):
        df = pd.read_csv(f)
        # Correlations should be matrix and error should be array
        df['bp_coefficient_correlations'] = df['bp_coefficient_correlations'].map(str_to_np_array)
        df['bp_coefficient_correlations'] = df.apply(lambda row: array_to_symmetric_matrix(row['bp_coefficient_correlations'], \
                                                     row['bp_n_parameters']), axis=1)
        df['bp_coefficient_errors'] = df['bp_coefficient_errors'].map(str_to_np_array)
        inverse = get_inverse_covariance_matrix(df, band='bp')
        npt.assert_array_almost_equal(inverse, solution)
