import unittest
from os.path import basename, join

import numpy as np
import numpy.testing as npt
from numpy import ndarray

from gaiaxpy.config.paths import filters_path
from gaiaxpy.core.config import get_file, load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.generator.internal_photometric_system import InternalPhotometricSystem

system = InternalPhotometricSystem('JKC')
system_label = system.get_system_label()


class TestConfig(unittest.TestCase):

    def test_get_file(self):
        _system = 'test'
        bp_model = 'v375wi'
        rp_model = 'v142r'
        file_path = get_file('filter', 'filter', _system, bp_model, rp_model)
        self.assertEqual(file_path, join(filters_path, basename(file_path)))

    def test_load_xpsampling_from_csv_type(self):
        xp_sampling = load_xpsampling_from_xml(system=system_label)
        self.assertIsInstance(xp_sampling, dict)

    def test_load_xpmerge_from_xml_types(self):
        xp_sampling_grid, xp_merge = load_xpmerge_from_xml(system=system_label)
        self.assertIsInstance(xp_merge, dict)
        self.assertIsInstance(xp_sampling_grid, np.ndarray)

    def test_load_xpoffset(self):
        # Standard system has got an offset file
        _system = InternalPhotometricSystem('JKC_Std')
        self.assertIsInstance(_system.get_offsets(), ndarray)
        npt.assert_array_equal(_system.get_offsets(),
                               np.array([2.44819e-19, 4.62320e-20, 1.81103e-20, 2.15027e-20, 1.73864e-20]))

        _system = InternalPhotometricSystem('SDSS_Std')
        self.assertIsInstance(_system.get_offsets(), ndarray)
        npt.assert_array_equal(_system.get_offsets(),
                               np.array([1.05000e-31, 2.47850e-32, 3.49926e-32, 3.80023e-32, 3.23519e-32]))

        _system = InternalPhotometricSystem('Stromgren_Std')
        self.assertIsInstance(_system.get_offsets(), ndarray)
        npt.assert_array_equal(_system.get_offsets(), np.zeros(3))
