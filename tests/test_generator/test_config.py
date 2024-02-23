import numpy as np
import numpy.testing as npt
import pytest
from numpy import ndarray

from gaiaxpy.core.config import load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.generator.internal_photometric_system import InternalPhotometricSystem

_rtol, _atol = 1e-24, 1e-24


def test_load_xpsampling_from_xml_type():
    system = InternalPhotometricSystem('Gaia_DR3_Vega')
    system_label = system.get_system_label()
    xp_sampling = load_xpsampling_from_xml(system=system_label)
    assert isinstance(xp_sampling, dict)


def test_load_xpmerge_from_xml_types():
    system = InternalPhotometricSystem('SDSS')
    xp_sampling_grid, xp_merge = load_xpmerge_from_xml(system=system.get_system_label())
    assert isinstance(xp_merge, dict)
    assert isinstance(xp_sampling_grid, np.ndarray)


def test_load_xpzeropoint_from_xml():
    system = InternalPhotometricSystem('JKC')
    npt.assert_array_equal(system.get_zero_points(), np.array([-25.9651, -25.4918, -26.0952, -26.6505, -27.3326]))
    npt.assert_array_equal(system.get_bands(), np.array(['U', 'B', 'V', 'R', 'I']))


@pytest.mark.parametrize('input_system,expected_offset', [
    ['JKC_Std', np.array([2.44819e-19, 4.62320e-20, 1.81103e-20, 2.15027e-20, 1.73864e-20])],
    ['SDSS_Std', np.array([1.05000e-31, 2.47850e-32, 3.49926e-32, 3.80023e-32, 3.23519e-32])],
    ['Stromgren_Std', np.zeros(3)]])
def test_load_xpoffset(input_system, expected_offset):
    # Standardised system has got an offset file
    xp_offset = InternalPhotometricSystem(input_system).offsets
    assert isinstance(xp_offset, ndarray)
    npt.assert_array_equal(xp_offset, expected_offset)
