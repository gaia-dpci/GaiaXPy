import numpy.testing as npt
import pytest
from numpy import ndarray

from gaiaxpy.photometric_system.photometric_system import (load_additional_systems, remove_additional_systems,
                                                           PhotometricSystem)
from tests.files.generator import additional_filters_dir
from tests.reference.generator import phot_systems_specs


@pytest.fixture(autouse=True)
def remove_systems():
    yield
    remove_additional_systems()


@pytest.fixture(scope='module')
def __ps():
    yield PhotometricSystem


def get_system_by_name(lst, name):
    return [item[1] for item in lst if item[0] == name][0]


@pytest.fixture(scope='module')
def available_systems():
    yield list(phot_systems_specs['name'])


@pytest.fixture()
def phot_systems(__ps):
    phot_system_names = [phot_system.name for phot_system in __ps]
    yield [(name, __ps[name]) for name in phot_system_names]


def test_system_is_standardised(__ps):
    """
    Check class assigned to each photometric system. Will raise an error if a system is missing in the solution
    dictionary.
    """
    all_phot_systems = [__ps[s] for s in __ps.get_available_systems(grouped=False).split(', ')]
    regular_systems = ['DR3_DECam', 'DR3_Els_Custom_W09_S2', 'DR3_Euclid_VIS', 'DR3_Gaia_2', 'DR3_Gaia_Vega',
                       'DR3_Halpha_Custom_AB', 'DR3_H_Custom', 'DR3_Hipparcos_Tycho', 'DR3_HST_ACSWFC',
                       'DR3_HST_HUGS_Std', 'DR3_HST_WFC3UVIS', 'DR3_HST_WFPC2', 'DR3_IPHAS', 'DR3_JKC', 'DR3_JKC_Std',
                       'DR3_JPAS', 'DR3_JPLUS', 'DR3_JWST_NIRCAM', 'DR3_LSST', 'DR3_PanSTARRS1', 'DR3_PanSTARRS1_Std',
                       'DR3_Pristine', 'DR3_SDSS', 'DR3_SDSS_Std', 'DR3_Sky_Mapper', 'DR3_Stromgren',
                       'DR3_Stromgren_Std', 'DR3_WFIRST']
    standardised_systems = ['DR3_HST_HUGS_Std', 'DR3_JKC_Std', 'DR3_PanSTARRS1_Std', 'DR3_SDSS_Std',
                            'DR3_Stromgren_Std']
    regular_dict = {s: 'RegularPhotometricSystem' for s in regular_systems}
    standardised_dict = {s: 'StandardisedPhotometricSystem' for s in standardised_systems}
    solution_dict = {**regular_dict, **standardised_dict}
    for system in all_phot_systems:
        assert system.value.__class__.__name__ == solution_dict[
            system.name], f'Test has failed for system {system.name}.'


def test_init(phot_systems, __ps):
    for name, phot_system in phot_systems:
        assert isinstance(phot_system, __ps)


def test_get_system_label(phot_systems, available_systems):
    for name in available_systems:
        # Photometric systems created by the package
        system = get_system_by_name(phot_systems, name)
        system_label = system.get_system_label()
        test_label = phot_systems_specs.loc[phot_systems_specs['name'] == name]['label'].iloc[0]
        assert isinstance(system_label, str)
        assert system_label == test_label


def test_bands(phot_systems, available_systems):
    for name in available_systems:
        # Photometric systems created by the package
        system = get_system_by_name(phot_systems, name)
        _test_bands = phot_systems_specs.loc[phot_systems_specs['name'] == name]['bands'].iloc[0]
        system_bands = system.get_bands()
        assert isinstance(system_bands, list)
        assert system_bands == _test_bands


def test_get_set_zero_points(phot_systems, available_systems):
    for name in available_systems:
        # Photometric systems created by the package
        system = get_system_by_name(phot_systems, name)
        test_zero_points = phot_systems_specs.loc[phot_systems_specs['name'] == name]['zero_points'].iloc[0]
        system_zero_points = system.get_zero_points()
        assert isinstance(system_zero_points, ndarray)
        npt.assert_array_equal(system_zero_points, test_zero_points)


def test_additional_systems_names(__ps):
    __ps = load_additional_systems(additional_filters_dir)
    ps = [__ps[s].get_system_name() for s in __ps.get_available_systems(grouped=False).split(', ') if
          s.startswith('USER')]
    assert set(ps) == {'USER_DR3_Panstarrs1Std_v1', 'USER_DR3_Sdss_v1', 'USER_DR3_Pristine_v1',
                       'USER_DR3_ASubstring_AndMore_v1', 'USER_DR3_ASubstring_v1'}
