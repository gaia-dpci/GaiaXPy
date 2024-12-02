import numpy.testing as npt
from gaiaxpy.generator.internal_photometric_system import InternalPhotometricSystem

from tests.test_generator.generator_paths import phot_systems_specs

# An InternalPhotometricSystem is created from a label, not from a name (i.e. from GaiaDr3Ab, not from GAIA_DR3_AB)
available_systems = list(phot_systems_specs['name'])
all_systems = [InternalPhotometricSystem(system) for system in available_systems]


def test_init():
    for system in all_systems:
        assert isinstance(system, InternalPhotometricSystem)


def test_get_bands():
    all_bands = list(phot_systems_specs['bands'])
    for system, test_bands in zip(all_systems, all_bands):
        assert system.get_bands() == test_bands


def test_get_system_label():
    all_labels = list(phot_systems_specs['label'])
    for system, test_labels in zip(all_systems, all_labels):
        assert system.get_system_label() == test_labels


def test_get_set_zero_points():
    all_zero_points = list(phot_systems_specs['zero_points'])
    for system, test_zero_points in zip(all_systems, all_zero_points):
        npt.assert_array_equal(system.get_zero_points(), test_zero_points)
