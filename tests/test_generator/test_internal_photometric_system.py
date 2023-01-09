import unittest
from os.path import join

import numpy as np
import numpy.testing as npt
import pandas as pd

from gaiaxpy.generator.internal_photometric_system import InternalPhotometricSystem
from tests.files.paths import files_path

phot_systems_specs = pd.read_csv(join(files_path, 'PhotometricSystemSpecs.csv'),
                                 converters={'bands': lambda x: x[1:-1].split(','),
                                             'zero_points': lambda y: np.array(y[1:-1].split(',')).astype(float)},
                                 float_precision='round_trip')

# An InternalPhotometricSystem is created from a label, not from a name (i.e. from GaiaDr3Ab, not from GAIA_DR3_AB)
available_systems = list(phot_systems_specs['name'])
all_systems = [InternalPhotometricSystem(system) for system in available_systems]


class TestInternalPhotometricSystem(unittest.TestCase):

    def test_init(self):
        for system in all_systems:
            self.assertIsInstance(system, InternalPhotometricSystem)

    def test_get_bands(self):
        all_bands = list(phot_systems_specs['bands'])
        for system, test_bands in zip(all_systems, all_bands):
            self.assertEqual(system.get_bands(), test_bands)

    def test_get_system_label(self):
        all_labels = list(phot_systems_specs['label'])
        for system, test_labels in zip(all_systems, all_labels):
            self.assertEqual(system.get_system_label(), test_labels)

    def test_get_set_zero_points(self):
        all_zero_points = list(phot_systems_specs['zero_points'])
        for system, test_zero_points in zip(all_systems, all_zero_points):
            npt.assert_array_equal(system.get_zero_points(), test_zero_points)
