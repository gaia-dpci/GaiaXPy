import numpy as np
import numpy.testing as npt
import pytest

from gaiaxpy.core.config import load_xpsampling_from_xml, load_xpmerge_from_xml
from gaiaxpy.generator.internal_photometric_system import InternalPhotometricSystem


def test_load_xpsampling_from_xml_type():
    xp_sampling = load_xpsampling_from_xml(system='Jkc')
    assert isinstance(xp_sampling, dict)


def test_load_xpmerge_from_xml_types():
    xp_sampling_grid, xp_merge = load_xpmerge_from_xml(system='Jkc')
    assert isinstance(xp_merge, dict)
    assert isinstance(xp_sampling_grid, np.ndarray)


def test_load_xpzeropoint_from_xml():
    system = InternalPhotometricSystem('Jkc')
    zero_points = system.get_zero_points()
    bands = system.get_bands()
    npt.assert_array_equal(zero_points, np.array([-25.9651, -25.4918, -26.0952, -26.6505, -27.3326]))
    npt.assert_array_equal(bands, np.array(['U', 'B', 'V', 'R', 'I']))


@pytest.mark.parametrize('system_value, solution', list(zip(['JkcStd', 'SdssStd', 'StromgrenStd'],
                                                            [np.array([2.44819e-19, 4.62320e-20, 1.81103e-20,
                                                                       2.15027e-20, 1.73864e-20]),
                                                             np.array([1.05000e-31, 2.47850e-32, 3.49926e-32,
                                                                       3.80023e-32, 3.23519e-32]), np.zeros(3)])))
def test_load_xpoffset(system_value, solution):
    # Standard systems have got an offset file
    system = InternalPhotometricSystem(system_value)
    xp_offset = system.get_offsets()
    assert isinstance(xp_offset, np.ndarray)
    npt.assert_array_equal(xp_offset, solution)
