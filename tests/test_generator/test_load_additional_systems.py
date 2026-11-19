import pytest

from gaiaxpy import load_additional_systems, generate, remove_additional_systems, PhotometricSystem
from tests.files.continuous import dr3_with_missing_bp_csv_file
from tests.files.generator import additional_filters_dir, additional_filters_dup_dir


@pytest.fixture(autouse=True)
def remove_systems():
    yield
    remove_additional_systems()


@pytest.fixture(scope='class')
def __ps():
    yield PhotometricSystem


def test_load_additional_with_err_corr(__ps):
    expected_columns = ['source_id', 'DR3_GaiaVega_mag_G', 'DR3_GaiaVega_mag_BP', 'DR3_GaiaVega_mag_RP',
                        'DR3_GaiaVega_flux_G', 'DR3_GaiaVega_flux_BP', 'DR3_GaiaVega_flux_RP',
                        'DR3_GaiaVega_flux_error_G', 'DR3_GaiaVega_flux_error_BP', 'DR3_GaiaVega_flux_error_RP']
    __ps = load_additional_systems(additional_filters_dir)
    phot_systems = [__ps.DR3_Gaia_Vega]
    photometry = generate(dr3_with_missing_bp_csv_file, photometric_system=phot_systems, error_correction=True,
                          save_file=False)
    assert len(photometry) == 3
    assert photometry['source_id'].to_list() == [5853498713190525696, 5405570973190252288, 5762406957886626816]
    assert list(photometry.columns) == expected_columns


def test_load_duplicate_additional_systems(__ps):
    # Check no system is loaded if there are duplicate files in the additional directory
    _available_systems = __ps.get_available_systems()
    with pytest.raises(ValueError):
        __ps = load_additional_systems(additional_filters_dup_dir)
    _new_available_systems = __ps.get_available_systems()
    assert _available_systems == _new_available_systems


def test_duplicate_names_in_dir(__ps):
    with pytest.raises(ValueError):
        load_additional_systems(additional_filters_dup_dir)


def _write_minimal_dr3_filter(filters_dir, system_name='TinyDr3', version='v1', extension='xml'):
    filter_path = filters_dir / f'{system_name}.gaiaxpy_dr3_{version}.{extension}'
    filter_path.write_text(
        '<config>'
        '<bands><item>G</item></bands>'
        '<fluxBias><value>0.0</value></fluxBias>'
        '<zeropoints><value>-56.1</value></zeropoints>'
        '</config>',
        encoding='utf-8'
    )
    return filter_path


def test_load_additional_dr3_xml(tmp_path):
    _write_minimal_dr3_filter(tmp_path)
    _write_minimal_dr3_filter(tmp_path, system_name='Test')

    photometric_systems = load_additional_systems(tmp_path)

    assert photometric_systems.USER_DR3_TinyDr3_v1.get_bands() == ['G']


def test_load_additional_dr3_xml(tmp_path):
    _write_minimal_dr3_filter(tmp_path)

    photometric_systems = load_additional_systems(tmp_path)

    assert photometric_systems.USER_DR3_TinyDr3_v1.get_bands() == ['G']


def test_load_additional_dr3_yaml_fails(tmp_path):
    _write_minimal_dr3_filter(tmp_path, extension='yaml')

    with pytest.raises(ValueError, match='Additional photometric systems must be DR3 XML filter files'):
        load_additional_systems(tmp_path)
