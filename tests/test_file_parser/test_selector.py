import pandas.testing as pdt
import pytest

from gaiaxpy.generator.generator import _generate, generate, PhotometricSystem
from tests.files.paths import mean_spectrum_avro_file

@pytest.fixture(scope='module')
def selected_source_id():
    yield 5853498713190525696


def select_records_with_value(record):
    # Field names should be the ones in the AVRO schema.
    return str(record['sourceId']).startswith('58')


def test_select_end_6(selected_source_id):
    ps = [PhotometricSystem.JKC, PhotometricSystem.JPAS]
    output = _generate(mean_spectrum_avro_file, photometric_system=ps, selector=select_records_with_value,
                       save_file=False)
    assert output['source_id'].iloc[0] == selected_source_id


def test_select_with_additional_columns(selected_source_id):
    ps = [PhotometricSystem.JKC, PhotometricSystem.JPAS]
    additional_columns = {'nuEff': ['specShape', 'nuEff'], 'nuEffError': ['specShape', 'nuEffError']}
    output = _generate(mean_spectrum_avro_file, photometric_system=ps, selector=select_records_with_value,
                       additional_columns=additional_columns, error_correction=True, save_file=False)
    regular_output = generate(mean_spectrum_avro_file, photometric_system=ps, additional_columns=additional_columns,
                              error_correction=True, save_file=False)
    pdt.assert_frame_equal(output, regular_output[regular_output['source_id'] == selected_source_id], check_like=True)
