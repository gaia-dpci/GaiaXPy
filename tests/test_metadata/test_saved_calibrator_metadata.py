import copy
import csv

import numpy as np
import pandas as pd
import pytest
from astropy.io import fits
from astropy.io.votable import parse_single_table
from astropy.table import Table
from fastavro import reader

from gaiaxpy.calibrator.calibrator import _calibrate
from gaiaxpy.core.custom_errors import InvalidReleaseError
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.core.generic_variables import VALID_EXTENSIONS, RELEASES
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.output import read_output_metadata
from gaiaxpy.output.metadata import FITS_METADATA_KEY
from gaiaxpy.output.sampled_spectra_data import SampledSpectraData
from tests.files.continuous import dr3_mean_spectra_csv_file


def read_values(path, extension):
    """Read numerical content with existing parsers or the format's native reader."""
    if extension == 'csv':
        return pd.read_csv(path,
                           converters={name: str_to_array for name in ('flux', 'flux_error', 'correlation')},
                           **CSV_FLOAT_PRECISION_KWARGS)
    if extension in ('ecsv', 'fits'):
        # Default-grid correlation arrays exceed Python csv's 128 KiB field limit.
        previous_limit = csv.field_size_limit()
        try:
            csv.field_size_limit(max(previous_limit, 10_000_000))
            table = Table.read(path, format='ascii.ecsv' if extension == 'ecsv' else 'fits')
        finally:
            csv.field_size_limit(previous_limit)
    elif extension == 'xml':
        table = parse_single_table(path).to_table(use_names_over_ids=True)
    else:
        with path.open('rb') as stream:
            records = list(reader(stream))
        for row in records:
            for name in ('flux', 'flux_error', 'correlation'):
                if name in row:
                    row[name] = str_to_array(row[name])
        return pd.DataFrame(records)
    return pd.DataFrame({name: list(table[name]) for name in table.colnames})


@pytest.fixture(params=RELEASES)
def calibrated(request):
    release = request.param
    if release == RELEASES.dr3:
        path = dr3_mean_spectra_csv_file
        output, sampling = _calibrate(path, sampling=None, with_correlation=True, save_file=False, disable_info=True)
    else:
        raise InvalidReleaseError(release)
    # Long descriptions and Unicode must survive FITS CONTINUE cards and XML escaping.
    output.attrs['gaiaxpy_metadata']['configuration_files'][0]['metadata']['description'] += (
            ' Unicode: α, é. Quotes: "example"; symbols: & < >. ' * 100)
    return output, sampling


@pytest.mark.parametrize('extension', VALID_EXTENSIONS)
def test_all_formats_preserve_complete_metadata_and_values(tmp_path, calibrated, extension):
    output, sampling = calibrated
    original = copy.deepcopy(output.attrs)
    data = SampledSpectraData(output, sampling)
    data.save(True, tmp_path, 'spectra', extension, 'csv')
    path = tmp_path / f'spectra.{extension}'
    metadata = read_output_metadata(path)
    assert metadata == original['gaiaxpy_metadata']
    assert output.attrs == original
    assert data.data.attrs == original
    metadata['configuration_files'][0]['metadata']['version'] = 'changed'
    assert read_output_metadata(path) == original['gaiaxpy_metadata']
    restored = read_values(path, extension)
    np.testing.assert_array_equal(restored['source_id'], output['source_id'])
    assert list(restored.columns) == list(output.columns)
    for name in ('flux', 'flux_error', 'correlation'):
        for actual, expected in zip(restored[name], output[name]):
            # Existing FITS/XML writers use float32 for flux_error.
            np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=0., equal_nan=True)


@pytest.mark.parametrize('extension', VALID_EXTENSIONS)
def test_outputs_without_metadata_remain_readable(tmp_path, calibrated, extension):
    output, sampling = calibrated
    output.attrs.pop('gaiaxpy_metadata')
    SampledSpectraData(output, sampling).save(True, tmp_path, 'legacy', extension, 'csv')
    path = tmp_path / f'legacy.{extension}'
    assert read_output_metadata(path) == {}
    restored = read_values(path, extension)
    np.testing.assert_array_equal(restored['source_id'], output['source_id'])


def test_csv_comment_is_accepted_by_existing_gaiaxpy_parser(tmp_path, calibrated):
    from gaiaxpy.file_parser.parse_generic import GenericParser
    output, sampling = calibrated
    SampledSpectraData(output, sampling).save(True, tmp_path, 'spectra', 'csv', 'csv')
    result = GenericParser()._parse_csv(tmp_path / 'spectra.csv', _array_columns=['flux', 'flux_error', 'correlation'])
    np.testing.assert_array_equal(result['source_id'], output['source_id'])


@pytest.mark.parametrize('extension', VALID_EXTENSIONS)
def test_invalid_metadata_fails_before_writing(tmp_path, calibrated, extension):
    output, sampling = calibrated
    output.attrs['gaiaxpy_metadata'] = ['not a dictionary']
    with pytest.raises(ValueError, match='must be a dictionary'):
        SampledSpectraData(output, sampling).save(True, tmp_path, 'invalid', extension, 'csv')
    assert not list(tmp_path.iterdir())


def test_malformed_and_duplicate_csv_metadata_raise(tmp_path):
    path = tmp_path / 'bad.csv'
    path.write_text('# gaiaxpy_metadata: {invalid}\nsource_id\n1\n')
    with pytest.raises(ValueError):
        read_output_metadata(path)
    path.write_text('# gaiaxpy_metadata: []\nsource_id\n1\n')
    with pytest.raises(ValueError, match='must be a dictionary'):
        read_output_metadata(path)
    path.write_text('# gaiaxpy_metadata: {}\n# gaiaxpy_metadata: {}\nsource_id\n1\n')
    with pytest.raises(ValueError, match='Duplicate'):
        read_output_metadata(path)


def test_missing_and_unsupported_files_raise(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_output_metadata(tmp_path / 'missing.csv')
    path = tmp_path / 'file.txt'
    path.touch()
    with pytest.raises(ValueError, match='Unsupported'):
        read_output_metadata(path)


def test_ecsv_with_empty_legacy_metadata_returns_empty_dictionary(tmp_path):
    path = tmp_path / 'legacy.ecsv'
    path.write_text('# %ECSV 1.0\n# ---\n# meta: null\nsource_id\n1\n')
    assert read_output_metadata(path) == {}


@pytest.mark.parametrize('extension', VALID_EXTENSIONS)
def test_present_invalid_metadata_is_not_treated_as_missing(tmp_path, extension):
    path = tmp_path / f'invalid.{extension}'
    if extension == 'csv':
        path.write_text('# gaiaxpy_metadata: null\nsource_id\n1\n')
    elif extension == 'ecsv':
        path.write_text('# %ECSV 1.0\n# ---\n# meta:\n#   gaiaxpy_metadata: null\nsource_id\n1\n')
    elif extension == 'fits':
        fits.PrimaryHDU(header=fits.Header({FITS_METADATA_KEY: 'null'})).writeto(path)
    elif extension == 'xml':
        path.write_text('<VOTABLE><RESOURCE><TABLE><PARAM name="gaiaxpy_metadata"/></TABLE></RESOURCE></VOTABLE>')
    else:
        from fastavro import writer
        schema = {'type': 'record', 'name': 'Test', 'fields': [{'name': 'source_id', 'type': 'long'}]}
        with path.open('wb') as stream:
            writer(stream, schema, [{'source_id': 1}], metadata={'gaiaxpy_metadata': 'null'})
    with pytest.raises(ValueError, match='must be a dictionary'):
        read_output_metadata(path)


def test_fits_reader_only_requires_primary_header(tmp_path):
    path = tmp_path / 'header.fits'
    fits.PrimaryHDU(header=fits.Header({FITS_METADATA_KEY: '{"example":1}'})).writeto(path)
    assert read_output_metadata(path) == {'example': 1}
