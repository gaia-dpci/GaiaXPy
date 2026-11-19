import copy

import numpy as np
import pandas as pd
import pytest
from astropy.io.votable import parse_single_table
from astropy.table import Table
from fastavro import reader

from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.core.custom_errors import InvalidReleaseError
from gaiaxpy.core.generic_variables import VALID_EXTENSIONS, RELEASES
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.output import read_output_metadata
from gaiaxpy.output.photometry_data import PhotometryData
from tests.files.continuous import dr3_mean_spectra_csv_file


def input_photometry(release):
    if release == RELEASES.dr3:
        frame = (pd.read_csv(dr3_mean_spectra_csv_file, **CSV_FLOAT_PRECISION_KWARGS)).iloc[:2].copy()
        systems = ([PhotometricSystem.DR3_SDSS_Std, PhotometricSystem.DR3_JKC_Std])
        return frame, systems
    else:
        raise InvalidReleaseError(release)


@pytest.fixture(params=RELEASES)
def photometry(request):
    frame, systems = input_photometry(request.param)
    output = generate(frame, systems, error_correction=True, save_file=False)
    output.attrs['gaiaxpy_metadata']['configuration_files'][0]['metadata']['description'] += (
            ' Unicode: α, é. Quotes: "example"; symbols: & < >. ' * 100)
    return output


def read_values(path, extension):
    if extension == 'csv':
        return pd.read_csv(path, **CSV_FLOAT_PRECISION_KWARGS)
    if extension in ('ecsv', 'fits'):
        return Table.read(path, format='ascii.ecsv' if extension == 'ecsv' else 'fits').to_pandas()
    if extension == 'xml':
        return parse_single_table(path).to_table(use_names_over_ids=True).to_pandas()
    with path.open('rb') as stream:
        return pd.DataFrame(list(reader(stream)))


def assert_values_equal(actual, expected, extension):
    assert list(actual.columns) == list(expected.columns)
    np.testing.assert_array_equal(actual['source_id'], expected['source_id'])
    for column in expected.columns.drop('source_id'):
        if '_within_range_' in column:
            assert pd.api.types.is_bool_dtype(actual[column])
            np.testing.assert_array_equal(actual[column], expected[column])
        else:
            # Existing AVRO fields and ECSV column declarations use float32.
            np.testing.assert_allclose(actual[column], expected[column], equal_nan=True,
                                       rtol=1e-6 if extension in ('avro', 'ecsv') else 1e-12, atol=0.)


@pytest.mark.parametrize('extension', VALID_EXTENSIONS)
def test_photometry_metadata_and_values_survive_saving(tmp_path, photometry, extension):
    original = copy.deepcopy(photometry.attrs)
    data = PhotometryData(photometry)
    data.save(True, tmp_path, 'photometry', extension, 'csv')
    path = tmp_path / f'photometry.{extension}'
    metadata = read_output_metadata(path)
    assert metadata == original['gaiaxpy_metadata']
    assert photometry.attrs == original
    assert data.data.attrs == original
    assert_values_equal(read_values(path, extension), photometry, extension)
    metadata['configuration_files'][0]['metadata']['version'] = 'edited'
    assert read_output_metadata(path) == original['gaiaxpy_metadata']


@pytest.mark.parametrize('extension', VALID_EXTENSIONS)
def test_legacy_photometry_without_metadata_remains_readable(tmp_path, photometry, extension):
    photometry.attrs.pop('gaiaxpy_metadata')
    PhotometryData(photometry).save(True, tmp_path, 'legacy', extension, 'csv')
    path = tmp_path / f'legacy.{extension}'
    assert read_output_metadata(path) == {}
    assert_values_equal(read_values(path, extension), photometry, extension)


@pytest.mark.parametrize('extension', VALID_EXTENSIONS)
def test_invalid_metadata_fails_before_output_is_created(tmp_path, photometry, extension):
    photometry.attrs['gaiaxpy_metadata'] = ['invalid']
    with pytest.raises(ValueError, match='must be a dictionary'):
        PhotometryData(photometry).save(True, tmp_path, 'invalid', extension, 'csv')
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('release', RELEASES)
@pytest.mark.parametrize('extension', VALID_EXTENSIONS)
def test_generate_saves_the_returned_metadata(tmp_path, release, extension):
    frame, systems = input_photometry(release)
    output = generate(frame, systems, error_correction=True, output_path=tmp_path,
                      output_file='generated', output_format=extension)
    path = tmp_path / f'generated.{extension}'
    assert read_output_metadata(path) == output.attrs['gaiaxpy_metadata']
    assert_values_equal(read_values(path, extension), output, extension)


def test_csv_metadata_comment_is_accepted_by_existing_parser(tmp_path, photometry):
    from gaiaxpy.file_parser.parse_generic import GenericParser
    PhotometryData(photometry).save(True, tmp_path, 'photometry', 'csv', 'csv')
    actual = GenericParser()._parse_csv(tmp_path / 'photometry.csv')
    assert_values_equal(actual, photometry, 'csv')
