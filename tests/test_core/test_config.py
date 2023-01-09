import unittest
from os.path import basename, join

import numpy as np
import numpy.testing as npt
from numpy import ndarray
import pytest

from gaiaxpy.config.paths import filters_path
from gaiaxpy.core.config import get_file
from gaiaxpy.generator.internal_photometric_system import InternalPhotometricSystem

system = InternalPhotometricSystem('JKC')
system_label = system.get_system_label()


class TestConfig(unittest.TestCase):

    def test_get_file(self):
        system = 'test'
        bp_model = 'v375wi'
        rp_model = 'v142r'
        file_path = get_file('filter', 'filter', system, bp_model, rp_model)
        self.assertEqual(file_path, join(filters_path, basename(file_path)))