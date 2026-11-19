from os.path import basename

import numpy as np
import numpy.testing as npt
import pytest

from gaiaxpy import PhotometricSystem
from gaiaxpy.core.config import load_xpmerge_from_file, load_xpsampling_from_file
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.photometric_system.internal_photometric_system import InternalPhotometricSystem

_rtol, _atol = 1e-24, 1e-24


def test_load_xpsampling_from_xml_type():
    system = InternalPhotometricSystem('Gaia_Vega', is_builtin=True, release=RELEASES.dr3)
    config_file = system.get_system_file()
    assert basename(config_file) == 'XpFilter_GaiaVega_v375wi_v142r.yaml'
    xp_sampling = load_xpsampling_from_file(config_file)
    assert isinstance(xp_sampling, dict)


def test_load_xpmerge_from_xml_types():
    system = InternalPhotometricSystem('SDSS', is_builtin=True, release=RELEASES.dr3)
    xp_sampling_grid, xp_merge = load_xpmerge_from_file(system.get_system_file())
    assert isinstance(xp_merge, dict)
    assert isinstance(xp_sampling_grid, np.ndarray)


def test_load_xpzeropoint_from_xml():
    system = InternalPhotometricSystem('JKC', is_builtin=True, release=RELEASES.dr3)
    npt.assert_array_equal(system.get_zero_points(), np.array([-25.9651, -25.4918, -26.0952, -26.6505, -27.3326]))
    npt.assert_array_equal(system.get_bands(), np.array(['U', 'B', 'V', 'R', 'I']))


def test_load_xpmerge_from_xml_types_cal():
    jkc = InternalPhotometricSystem('JKC', is_builtin=True, release=RELEASES.dr3)
    config_file = jkc.get_system_file()
    assert config_file.name == 'XpFilter_Jkc_v375wi_v142r.yaml'
    xp_sampling_grid, xp_merge = load_xpmerge_from_file(config_file)
    assert isinstance(xp_merge, dict)
    assert isinstance(xp_sampling_grid, np.ndarray)


def test_load_xpzeropoint_from_xml_cal():
    system = InternalPhotometricSystem('Jkc', is_builtin=True, release=RELEASES.dr3)
    zero_points = system.get_zero_points()
    bands = system.get_bands()
    npt.assert_array_equal(zero_points, np.array([-25.9651, -25.4918, -26.0952, -26.6505, -27.3326]))
    npt.assert_array_equal(bands, np.array(['U', 'B', 'V', 'R', 'I']))


@pytest.mark.parametrize('system_name,expected_offsets', [
    ('JkcStd', [2.44819e-19, 4.62320e-20, 1.81103e-20, 2.15027e-20, 1.73864e-20]),
    ('JKC_Std', [2.44819e-19, 4.62320e-20, 1.81103e-20, 2.15027e-20, 1.73864e-20]),
    ('SdssStd', [1.05000e-31, 2.47850e-32, 3.49926e-32, 3.80023e-32, 3.23519e-32]),
    ('SDSS_Std', [1.05000e-31, 2.47850e-32, 3.49926e-32, 3.80023e-32, 3.23519e-32]),
    ('StromgrenStd', [0., 0., 0.]),
    ('Stromgren_Std', [0., 0., 0.])
])
def test_get_offsets_dr3(system_name, expected_offsets):
    system = InternalPhotometricSystem(system_name, is_builtin=True, release=RELEASES.dr3)
    offsets = system.get_offsets()
    assert isinstance(offsets, np.ndarray)
    assert offsets.shape == (len(system.get_bands()),)
    npt.assert_array_equal(offsets, expected_offsets)


@pytest.mark.parametrize('system_name,expected_offsets', [
    ('DR3_JKC_Std', [2.44819e-19, 4.62320e-20, 1.81103e-20, 2.15027e-20, 1.73864e-20]),
    ('DR3_SDSS_Std', [1.05000e-31, 2.47850e-32, 3.49926e-32, 3.80023e-32, 3.23519e-32]),
    ('DR3_Stromgren_Std', [0., 0., 0.])
])
def test_public_get_offsets_dr3(system_name, expected_offsets):
    system = getattr(PhotometricSystem, system_name)
    offsets = system.get_offsets()
    assert isinstance(offsets, np.ndarray)
    assert offsets.shape == (len(system.get_bands()),)
    npt.assert_array_equal(offsets, expected_offsets)
