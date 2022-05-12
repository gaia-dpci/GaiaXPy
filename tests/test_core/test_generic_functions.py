import unittest
import numpy as np
from gaiaxpy.core import array_to_symmetric_matrix, _validate_pwl_sampling

array = np.array([1, 2, 3, 4, 5, 6])
size = 3


class TestGenericFunctions(unittest.TestCase):

    def test_validate_pwl_sampling_upper_limit(self):
        sampling = np.linspace(0, 71, 300)
        with self.assertRaises(ValueError):
            _validate_pwl_sampling(sampling)

    def test_validate_pwl_sampling_lower_limit(self):
        sampling = np.linspace(-11, 70, 300)
        with self.assertRaises(ValueError):
            _validate_pwl_sampling(sampling)

    def test_validate_pwl_sampling_len_zero(self):
        sampling = np.linspace(0, 0, 0)
        with self.assertRaises(ValueError):
            _validate_pwl_sampling(sampling)

    def test_validate_pwl_sampling_none(self):
        sampling = None
        with self.assertRaises(ValueError):
            _validate_pwl_sampling(sampling)

    def test_validate_pwl_sampling(self):
        sampling = np.array([0.3, 0.2, 0.5])
        with self.assertRaises(ValueError):
            _validate_pwl_sampling(sampling)


class TestArrayToSymmetricMatrix(unittest.TestCase):

    def test_array_to_symmetric_matrix_type(self):
        self.assertIsInstance(
            array_to_symmetric_matrix(
                size, array), np.ndarray)

    def test_array_to_symmetric_matrix_values(self):
        array = np.array([4, 5, 6])
        expected_symmetric = np.array(
            [[1., 4., 5.], [4., 1., 6.], [5., 6., 1.]])
        self.assertTrue(
            (array_to_symmetric_matrix(
                size, array) == expected_symmetric).all())

    def test_array_to_symmetric_matrix_mismatching(self):
        with self.assertRaises(ValueError):
            array_to_symmetric_matrix(2, array)

    def test_array_to_symmetric_matrix_negative_size(self):
        with self.assertRaises(ValueError):
            array_to_symmetric_matrix(-1, array)

    def test_array_to_symmetric_matrix_wrong__tipe(self):
        with self.assertRaises(TypeError):
            array_to_symmetric_matrix(size, size)
        with self.assertRaises(TypeError):
            array_to_symmetric_matrix(array, array)
