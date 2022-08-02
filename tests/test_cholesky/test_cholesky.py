import unittest
import numpy as np
import numpy.testing as npt
from os.path import join
from gaiaxpy import get_inverse_covariance_matrix
from tests.files import files_path


class TestCholesky(unittest.TestCase):

    def test_inverse_covariance_matrix_file_from_notebook(self):
        f = join(files_path, 'cholesky', '18Sco-XP-spectra.csv')
        inverse = get_inverse_covariance_matrix(f, band='bp')
        # Load solution
        solution = np.loadtxt(join(files_path, 'cholesky', 'nb_bp_get_inv_cov_mat.txt'))
        npt.assert_array_almost_equal(inverse, solution)
