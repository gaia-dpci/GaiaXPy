import numpy.testing as npt
import pytest
from numpy import ndarray

from gaiaxpy import generate
from gaiaxpy.core.generic_functions import _get_built_in_systems
from gaiaxpy.generator.photometric_system import PhotometricSystem, load_additional_systems, remove_additional_systems
from tests.files.paths import with_missing_bp_ecsv_file
from tests.test_generator.generator_paths import additional_filters_dir
from tests.test_generator.test_internal_photometric_system import phot_systems_specs


def get_system_by_name(lst, name):
    return [item[1] for item in lst if item[0] == name][0]


@pytest.fixture(scope='module')
def available_systems():
    yield list(phot_systems_specs['name'])


@pytest.fixture()
def phot_systems():
    phot_system_names = [phot_system.name for phot_system in PhotometricSystem]
    yield [(name, PhotometricSystem[name]) for name in phot_system_names]


def test_system_is_standardised():
    """
    Check class assigned to each photometric system. Will raise an error if a system is missing in the solution
    dictionary.
    """
    PhotometricSystem = remove_additional_systems()  # Ensure only built-in systems are present
    all_phot_systems = [PhotometricSystem[s] for s in PhotometricSystem.get_available_systems().split(', ')]
    regular_systems = ["DECam", "Els_Custom_W09_S2", "Euclid_VIS", "Gaia_2", "Gaia_DR3_Vega", "Halpha_Custom_AB",
                       "H_Custom", "Hipparcos_Tycho", "HST_ACSWFC", "HST_WFC3UVIS", "HST_WFPC2", "IPHAS", "JKC",
                       "JPAS", "JPLUS", "JWST_NIRCAM", "LSST", "PanSTARRS1", "Pristine", "SDSS", "Sky_Mapper",
                       "Stromgren", "WFIRST"]
    standardised_systems = ["HST_HUGS_Std", "JKC_Std", "PanSTARRS1_Std", "SDSS_Std", "Stromgren_Std"]
    regular_dict = {s: "RegularPhotometricSystem" for s in regular_systems}
    standardised_dict = {s: "StandardisedPhotometricSystem" for s in standardised_systems}
    solution_dict = {**regular_dict, **standardised_dict}
    for system in all_phot_systems:
        assert system.value.__class__.__name__ == solution_dict[system.name], \
            f'Test has failed for system {system.name}.'


def test_init(phot_systems):
    for name, phot_system in phot_systems:
        assert isinstance(phot_system, PhotometricSystem)


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


def test_user_interaction():
    PhotometricSystem = remove_additional_systems()  # Ensure only built-in systems are present
    phot_system_list = [s for s in PhotometricSystem.get_available_systems().split(', ')]
    built_in_systems = _get_built_in_systems()
    assert set(phot_system_list) == set(built_in_systems)
    __PhotometricSystem = load_additional_systems(additional_filters_dir)
    new_phot_systems = [s for s in __PhotometricSystem.get_available_systems().split(', ')]
    assert len(phot_system_list) + 4 == len(new_phot_systems)
    ps = [__PhotometricSystem[s] for s in ['Pristine', 'SDSS', 'PanSTARRS1_Std', 'USER_Panstarrs1Std', 'USER_Sdss',
                                           'USER_Pristine']]
    output = generate(with_missing_bp_ecsv_file, photometric_system=ps, save_file=False)
    built_in_columns = [c for c in output.columns if not c.startswith('USER')]
    built_in_columns.remove('source_id')
    for column in built_in_columns:
        npt.assert_array_equal(output[column].values, output[f'USER_{column}'].values)
    __PhotometricSystem = remove_additional_systems()
    phot_system_list = [s for s in __PhotometricSystem.get_available_systems().split(', ')]
    assert set(phot_system_list) == set(built_in_systems)


def test_additional_systems_names():
    global PhotometricSystem
    PhotometricSystem = remove_additional_systems()
    PhotometricSystem = load_additional_systems(additional_filters_dir)
    ps = [PhotometricSystem[s].get_system_name() for s in PhotometricSystem.get_available_systems().split(', ') if
          s.startswith('USER')]
    assert ps == ['USER_Panstarrs1Std', 'USER_Sdss', 'USER_Pristine', 'USER_AFilter']
