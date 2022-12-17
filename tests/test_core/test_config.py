import unittest
from os.path import basename, join, dirname, realpath

import numpy as np
import numpy.testing as npt
from numpy import ndarray
import pytest

from gaiaxpy import load_additional_systems
from gaiaxpy.config.paths import filters_path
from gaiaxpy.core.config import get_file, _load_offset_from_xml, _load_xpmerge_from_xml, _load_xpsampling_from_xml, \
    _load_xpzeropoint_from_xml
from tests.files.paths import files_path

system_value = 'Jkc'

xp_sampling = _load_xpsampling_from_xml(system=system_value)
xp_sampling_grid, xp_merge = _load_xpmerge_from_xml(system=system_value)
xp_zero_point = _load_xpzeropoint_from_xml(system_value)


class TestConfig(unittest.TestCase):

    def test_get_file(self):
        system = 'test'
        bp_model = 'v375wi'
        rp_model = 'v142r'
        file_path = get_file('filter', 'filter', system, bp_model, rp_model)
        self.assertEqual(file_path, join(filters_path, basename(file_path)))

    def test_load_xpsampling_from_csv_type(self):
        self.assertIsInstance(xp_sampling, dict)

    def test_load_xpmerge_from_xml_types(self):
        self.assertIsInstance(xp_merge, dict)
        self.assertIsInstance(xp_sampling_grid, np.ndarray)

    def test_load_xpzeropoint_from_xml(self):
        self.assertIsInstance(xp_zero_point, tuple)
        bands, zero_points = xp_zero_point
        npt.assert_array_equal(zero_points, np.array([-25.9651, -25.4918, -26.0952, -26.6505, -27.3326]))
        npt.assert_array_equal(bands, np.array(['U', 'B', 'V', 'R', 'I']))

    def test_load_xpoffset(self):
        # Standard system has got an offset file
        system_value = 'JkcStd'
        xp_offset = _load_offset_from_xml(system_value)
        self.assertIsInstance(xp_offset, ndarray)
        npt.assert_array_equal(xp_offset, np.array([2.44819e-19, 4.62320e-20, 1.81103e-20, 2.15027e-20, 1.73864e-20]))

        system_value = 'SdssStd'
        xp_offset = _load_offset_from_xml(system_value)
        self.assertIsInstance(xp_offset, ndarray)
        npt.assert_array_equal(xp_offset, np.array([1.05000e-31, 2.47850e-32, 3.49926e-32, 3.80023e-32, 3.23519e-32]))

        system_value = 'StromgrenStd'
        xp_offset = _load_offset_from_xml(system_value)
        self.assertIsInstance(xp_offset, ndarray)
        npt.assert_array_equal(xp_offset, np.zeros(3))

'''
def test_additional_config(tmpdir):
    # TODO: Should use a temporary path
    config_file = join(tmpdir, '.testrc')
    load_additional_systems(filters_path=join(files_path, 'additional_filters'), config_file=config_file)
    system = 'test'
    bp_model = 'v375wi'
    rp_model = 'v142r'
    file_path = get_file('filter', 'filter', system, bp_model, rp_model, config_file=config_file)
    print(file_path)
    # self.assertEqual(file_path, join(filters_path, basename(file_path)))
'''