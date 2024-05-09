import pytest

from gaiaxpy import load_additional_systems, generate, remove_additional_systems
from tests.files.paths import with_missing_bp_csv_file
from tests.test_generator.generator_paths import additional_filters_dir


@pytest.fixture(scope='class')
def __ps():
    PhotometricSystem = remove_additional_systems()
    yield PhotometricSystem


def test_load_additional_with_err_corr(__ps):
    expected_columns = ['source_id', 'GaiaDr3Vega_mag_G', 'GaiaDr3Vega_mag_BP', 'GaiaDr3Vega_mag_RP',
                        'GaiaDr3Vega_flux_G', 'GaiaDr3Vega_flux_BP', 'GaiaDr3Vega_flux_RP', 'GaiaDr3Vega_flux_error_G',
                        'GaiaDr3Vega_flux_error_BP', 'GaiaDr3Vega_flux_error_RP']
    __ps = load_additional_systems(additional_filters_dir)
    phot_systems = [__ps.Gaia_DR3_Vega]
    photometry = generate(with_missing_bp_csv_file, photometric_system=phot_systems, error_correction=True,
                          save_file=False)
    assert len(photometry) == 3
    assert photometry['source_id'].to_list() == [5853498713190525696, 5405570973190252288, 5762406957886626816]
    assert list(photometry.columns) == expected_columns
