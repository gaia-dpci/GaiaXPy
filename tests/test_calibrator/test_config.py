import unittest

import numpy as np
import numpy.testing as npt

from gaiaxpy.core.config import load_xpsampling_from_xml, load_xpmerge_from_xml
from gaiaxpy.generator.internal_photometric_system import InternalPhotometricSystem


class TestConfig(unittest.TestCase):

    def test_load_xpsampling_from_xml_type(self):
        system_value = 'Jkc'
        xp_sampling = load_xpsampling_from_xml(system=system_value)
        self.assertIsInstance(xp_sampling, dict)

    def test_load_xpmerge_from_xml_types(self):
        system_value = 'Jkc'
        xp_sampling_grid, xp_merge = load_xpmerge_from_xml(system=system_value)
        self.assertIsInstance(xp_merge, dict)
        self.assertIsInstance(xp_sampling_grid, np.ndarray)

    def test_load_xpzeropoint_from_xml(self):
        system_value = 'Jkc'
        system = InternalPhotometricSystem(system_value)
        zero_points = system.get_zero_points()
        bands = system.get_bands()
        self.assertIsInstance(zero_points, np.ndarray)
        npt.assert_array_equal(zero_points, np.array([-25.9651, -25.4918, -26.0952, -26.6505, -27.3326]))
        npt.assert_array_equal(bands, np.array(['U', 'B', 'V', 'R', 'I']))

    def test_load_xpoffset(self):
        system_values = ['JkcStd', 'SdssStd', 'StromgrenStd']
        solutions = [np.array([2.44819e-19, 4.62320e-20, 1.81103e-20, 2.15027e-20, 1.73864e-20]),
                     np.array([1.05000e-31, 2.47850e-32, 3.49926e-32, 3.80023e-32, 3.23519e-32]),
                     np.zeros(3)]
        # Standard systems have got an offset file
        for value, solution in zip(system_values, solutions):
            system = InternalPhotometricSystem(value)
            xp_offset = system.get_offsets()
            self.assertIsInstance(xp_offset, np.ndarray)
            npt.assert_array_equal(xp_offset, solution)
