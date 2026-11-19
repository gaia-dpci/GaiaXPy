import pandas.testing as pdt
import pytest

from gaiaxpy.generator.generator import _generate, generate
from gaiaxpy.photometric_system.photometric_system import PhotometricSystem
from tests.files.continuous import dr3_mean_spectra_avro_file


@pytest.fixture(scope='module')
def selected_source_id():
    yield 5853498713190525696


def select_records_with_value(record):
    # Field names should be the ones in the AVRO schema.
    return str(record['sourceId']).startswith('58')


def test_select_end_6(selected_source_id):
    ps = [PhotometricSystem.DR3_JKC, PhotometricSystem.DR3_JPAS]
    output = _generate(dr3_mean_spectra_avro_file, photometric_system=ps, save_file=False,
                       selector=select_records_with_value, release='dr3')
    assert output['source_id'].iloc[0] == selected_source_id


def test_select_with_additional_columns(selected_source_id):
    ps = [PhotometricSystem.DR3_JKC, PhotometricSystem.DR3_JPAS]
    additional_columns = {'nuEff': ['specShape', 'nuEff'], 'nuEffError': ['specShape', 'nuEffError']}
    output = _generate(dr3_mean_spectra_avro_file, photometric_system=ps, save_file=False, error_correction=True,
                       additional_columns=additional_columns, selector=select_records_with_value, release='dr3')
    regular_output = generate(dr3_mean_spectra_avro_file, photometric_system=ps, save_file=False, error_correction=True,
                              additional_columns=additional_columns)
    pdt.assert_frame_equal(output, regular_output[regular_output['source_id'] == selected_source_id], check_like=True)
