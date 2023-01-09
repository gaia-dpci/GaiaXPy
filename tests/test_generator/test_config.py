import unittest

import numpy as np
import numpy.testing as npt
from numpy import ndarray

from gaiaxpy.core.config import _load_xpmerge_from_xml, _load_xpsampling_from_xml
from gaiaxpy.generator.internal_photometric_system import InternalPhotometricSystem

# Non-standard system
system = InternalPhotometricSystem('JKC')
system_label = system.get_system_label()

_rtol, _atol = 1e-24, 1e-24


class TestConfig(unittest.TestCase):

    def test_load_xpsampling_from_xml_type(self):
        xp_sampling = _load_xpsampling_from_xml(system=system_label)
        self.assertIsInstance(xp_sampling, dict)

    def test_load_xpmerge_from_xml_types(self):
        xp_sampling_grid, xp_merge = _load_xpmerge_from_xml(system=system_label)
        self.assertIsInstance(xp_merge, dict)
        self.assertIsInstance(xp_sampling_grid, np.ndarray)

    def test_load_xpzeropoint_from_xml(self):
        zero_points = system.get_zero_points()
        bands = system.get_bands()
        npt.assert_array_equal(zero_points, np.array([-25.9651, -25.4918, -26.0952, -26.6505, -27.3326]))
        npt.assert_array_equal(bands, np.array(['U', 'B', 'V', 'R', 'I']))

    def test_load_xpoffset(self):

        # Standard system has got an offset file
        system = InternalPhotometricSystem('JKC_Std')
        xp_offset = system.offsets
        self.assertIsInstance(xp_offset, ndarray)
        npt.assert_array_equal(xp_offset, np.array([2.44819e-19, 4.62320e-20, 1.81103e-20, 2.15027e-20, 1.73864e-20]))

        system = InternalPhotometricSystem('SDSS_Std')
        xp_offset = system.offsets
        self.assertIsInstance(xp_offset, ndarray)
        npt.assert_array_equal(xp_offset, np.array([1.05000e-31, 2.47850e-32, 3.49926e-32, 3.80023e-32, 3.23519e-32]))

        system = InternalPhotometricSystem('Stromgren_Std')
        xp_offset = system.offsets
        self.assertIsInstance(xp_offset, ndarray)
        npt.assert_array_equal(xp_offset, np.zeros(3))
