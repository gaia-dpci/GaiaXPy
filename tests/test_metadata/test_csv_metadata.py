"""CSV tables and metadata companions must both be ordinary readable CSV files."""
import csv
import json
from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from gaiaxpy.output import read_output_metadata
from gaiaxpy.output.photometry_data import PhotometryData
from gaiaxpy.output.sampled_spectra_data import SampledSpectraData


@pytest.fixture(params=['photometry', 'sampled'])
def output(request):
    frame = pd.DataFrame({'source_id': [5853498713190525696, 5762406957886626816], 'value': [1.25, 2.5]})
    frame.attrs['gaiaxpy_metadata'] = {
        'schema_version': 1, 'gaiaxpy_version': 'test', 'data_release': 'dr3',
        'description': 'α, é; quotes "example"\nsecond line # retained',
        'configuration_files': [{'file': 'Example.yaml', 'metadata': {'version': '1'}}],
        'enabled': True, 'missing': None, 'empty': {}, 'bands': ['G', 'BP'], 'numeric_label': '001'}
    if request.param == 'photometry':
        return PhotometryData(frame)
    if request.param == 'sampled':
        frame['flux'] = [np.array([1., 2.]), np.array([3., 4.])]
        return SampledSpectraData(frame, np.array([500., 600.]))


def save(output, tmp_path):
    output.save(True, tmp_path, 'result', 'csv', 'csv', disable_info=True)


def test_plain_pandas_reads_both_csv_files_and_metadata_round_trips(output, tmp_path):
    before = deepcopy(output.data.attrs)
    save(output, tmp_path)
    frame = pd.read_csv(tmp_path / 'result.csv')
    assert list(frame.columns) == list(output.data.columns)
    assert frame['source_id'].tolist() == output.data['source_id'].tolist()
    assert frame['value'].tolist() == output.data['value'].tolist()
    companion = tmp_path / 'result_metadata.csv'
    metadata_frame = pd.read_csv(companion, keep_default_na=False)
    assert list(metadata_frame.columns) == ['field', 'value', 'type']
    recovered = {row.field: row.value if row.type == 'string' else json.loads(row.value)
                 for row in metadata_frame.itertuples()}
    assert recovered == before['gaiaxpy_metadata']
    assert read_output_metadata(tmp_path / 'result.csv') == recovered
    assert output.data.attrs == before
    assert not list(tmp_path.glob('*.json'))
    assert not list(tmp_path.glob('*.metadata*'))
    if isinstance(output, SampledSpectraData):
        assert (tmp_path / 'result_sampling.csv').is_file()


def test_overwriting_updates_metadata_and_removes_stale_companion(output, tmp_path):
    save(output, tmp_path)
    output.data.attrs['gaiaxpy_metadata'] = {'version': '2'}
    save(output, tmp_path)
    assert read_output_metadata(tmp_path / 'result.csv') == {'version': '2'}
    output.data.attrs.pop('gaiaxpy_metadata')
    save(output, tmp_path)
    assert not (tmp_path / 'result_metadata.csv').exists()
    assert read_output_metadata(tmp_path / 'result.csv') == {}
    assert len(pd.read_csv(tmp_path / 'result.csv')) == 2


def test_no_metadata_creates_only_data_and_optional_sampling(output, tmp_path):
    output.data.attrs.pop('gaiaxpy_metadata')
    save(output, tmp_path)
    assert not (tmp_path / 'result_metadata.csv').exists()
    assert read_output_metadata(tmp_path / 'result.csv') == {}


def test_empty_metadata_remains_a_valid_companion(output, tmp_path):
    output.data.attrs['gaiaxpy_metadata'] = {}
    save(output, tmp_path)
    assert list(pd.read_csv(tmp_path / 'result_metadata.csv').columns) == ['field', 'value', 'type']
    assert read_output_metadata(tmp_path / 'result.csv') == {}


def test_invalid_metadata_does_not_overwrite_existing_files(output, tmp_path):
    save(output, tmp_path)
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    output.data.attrs['gaiaxpy_metadata'] = {'bad': float('nan')}
    with pytest.raises(ValueError):
        save(output, tmp_path)
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_large_metadata_fields_restore_csv_field_limit(output, tmp_path):
    output.data.attrs['gaiaxpy_metadata'] = {'description': 'α' * 200_000}
    save(output, tmp_path)
    before = csv.field_size_limit()
    assert read_output_metadata(tmp_path / 'result.csv') == output.data.attrs['gaiaxpy_metadata']
    assert csv.field_size_limit() == before


@pytest.mark.parametrize('content', [
    '', 'key,value\na,1\n', 'field,value\na,1\na,2\n',
    'field,value\na,invalid\n', 'field,value\na\n', 'field,value\n,1\n',
    'field,value\na,1,extra\n', 'field,value\na,"unterminated\n'])
def test_malformed_companions_raise_instead_of_disappearing(content, tmp_path):
    path = tmp_path / 'result.csv'
    path.write_text('source_id\n1\n')
    (tmp_path / 'result_metadata.csv').write_text(content)
    before = csv.field_size_limit()
    with pytest.raises(ValueError, match='result_metadata.csv'):
        read_output_metadata(path)
    assert csv.field_size_limit() == before


def test_legacy_embedded_csv_metadata_is_still_readable(tmp_path):
    path = tmp_path / 'legacy.csv'
    path.write_text('# gaiaxpy_metadata: {"version":"old"}\nsource_id\n1\n')
    assert read_output_metadata(path) == {'version': 'old'}


@pytest.mark.parametrize('value', ['', '001', '1', '1.0', 'true', 'false', 'null', '[]', '{}',
                                   '"quoted"', 'α, é\nsecond line'])
def test_strings_remain_strings_without_json_quotes(tmp_path, value):
    frame = pd.DataFrame({'source_id': [1]})
    frame.attrs['gaiaxpy_metadata'] = {'label': value}
    PhotometryData(frame).save(True, tmp_path, 'result', 'csv', 'csv', disable_info=True)
    with (tmp_path / 'result_metadata.csv').open(newline='', encoding='utf-8') as stream:
        assert list(csv.reader(stream)) == [['field', 'value', 'type'], ['label', value, 'string']]
    recovered = read_output_metadata(tmp_path / 'result.csv')
    assert recovered == {'label': value}
    assert type(recovered['label']) is str


def test_simple_strings_are_readable_in_the_raw_csv(tmp_path):
    frame = pd.DataFrame({'source_id': [1]})
    frame.attrs['gaiaxpy_metadata'] = {'schema_version': 1, 'function': 'calibrate',
                                       'gaiaxpy_version': '2.1.2', 'data_release': 'dr3'}
    PhotometryData(frame).save(True, tmp_path, 'result', 'csv', 'csv', disable_info=True)
    assert (tmp_path / 'result_metadata.csv').read_text().splitlines() == [
        'field,value,type', 'schema_version,1,integer', 'function,calibrate,string',
        'gaiaxpy_version,2.1.2,string', 'data_release,dr3,string']


def test_typed_scalars_preserve_their_python_types(tmp_path):
    metadata = {'integer': 1, 'number': 1.0, 'enabled': True, 'disabled': False, 'missing': None,
                'array': [1, '001', None, {'nested': True}], 'object': {'label': 'null'}}
    frame = pd.DataFrame({'source_id': [1]})
    frame.attrs['gaiaxpy_metadata'] = metadata
    PhotometryData(frame).save(True, tmp_path, 'result', 'csv', 'csv', disable_info=True)
    recovered = read_output_metadata(tmp_path / 'result.csv')
    assert recovered == metadata
    assert {field: type(value) for field, value in recovered.items()} == {
        field: type(value) for field, value in metadata.items()}


def test_legacy_two_column_metadata_companions_are_still_readable(tmp_path):
    path = tmp_path / 'result.csv'
    path.write_text('source_id\n1\n')
    metadata = {'function': 'calibrate', 'version': '001', 'enabled': True, 'missing': None,
                'configuration_files': [{'file': 'Example.yaml'}]}
    with (tmp_path / 'result_metadata.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['field', 'value'])
        writer.writerows((field, json.dumps(value)) for field, value in metadata.items())
    assert read_output_metadata(path) == metadata


@pytest.mark.parametrize('row', [['a', 'text', 'unknown'], ['a', 'true', 'integer'],
                                 ['a', '1', 'boolean'], ['a', '[]', 'object'],
                                 ['a', '{}', 'array'], ['a', 'null', 'string', 'extra'],
                                 ['', '1', 'integer'], ['a', 'invalid', 'number'],
                                 ['a', '1', 'integer'], ['a', '1']])
def test_malformed_typed_companions_raise(row, tmp_path):
    path = tmp_path / 'result.csv'
    path.write_text('source_id\n1\n')
    with (tmp_path / 'result_metadata.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['field', 'value', 'type'])
        writer.writerow(row)
        if row == ['a', '1', 'integer']:
            writer.writerow(row)  # Duplicate field.
    with pytest.raises(ValueError, match='result_metadata.csv'):
        read_output_metadata(path)


@pytest.mark.parametrize('as_string', [False, True], ids=['path', 'str'])
def test_main_and_metadata_paths_return_the_same_dictionary(output, tmp_path, as_string):
    save(output, tmp_path)
    main = tmp_path / 'result.csv'
    companion = tmp_path / 'result_metadata.csv'
    first = read_output_metadata(str(main) if as_string else main)
    second = read_output_metadata(str(companion) if as_string else companion)
    assert first == second == output.data.attrs['gaiaxpy_metadata']
    second['configuration_files'][0]['metadata']['version'] = 'changed'
    assert first['configuration_files'][0]['metadata']['version'] == '1'
    assert read_output_metadata(companion) == output.data.attrs['gaiaxpy_metadata']


def test_metadata_companion_can_be_read_without_the_main_file(output, tmp_path):
    save(output, tmp_path)
    (tmp_path / 'result.csv').unlink()
    assert read_output_metadata(tmp_path / 'result_metadata.csv') == output.data.attrs['gaiaxpy_metadata']


def test_direct_metadata_path_accepts_uppercase_filename_and_extension(tmp_path):
    path = tmp_path / 'RESULT_METADATA.CSV'
    path.write_text('field,value,type\nfunction,calibrate,string\n')
    assert read_output_metadata(path) == {'function': 'calibrate'}


def test_direct_legacy_companion_can_be_read_without_main_file(tmp_path):
    path = tmp_path / 'result_metadata.csv'
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['field', 'value'])
        writer.writerow(['function', json.dumps('calibrate')])
        writer.writerow(['configuration_files', json.dumps([{'file': 'Example.yaml'}])])
    assert read_output_metadata(path) == {'function': 'calibrate',
                                          'configuration_files': [{'file': 'Example.yaml'}]}


@pytest.mark.parametrize('header', ['field,value', 'field,value,type'])
def test_direct_empty_companion_returns_an_empty_dictionary(header, tmp_path):
    path = tmp_path / 'result_metadata.csv'
    path.write_text(header + '\n')
    assert read_output_metadata(path) == {}


@pytest.mark.parametrize('content', ['', 'source_id\n1\n', 'field,value\nfunction,invalid\n',
                                     'field,value,type\nfunction,calibrate,unknown\n',
                                     'field,value,type\nversion,1,integer\nversion,2,integer\n'])
def test_malformed_direct_companion_raises_instead_of_returning_empty(content, tmp_path):
    path = tmp_path / 'result_metadata.csv'
    path.write_text(content)
    before = csv.field_size_limit()
    with pytest.raises(ValueError, match='result_metadata.csv'):
        read_output_metadata(path)
    assert csv.field_size_limit() == before


def test_missing_direct_companion_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match='result_metadata.csv'):
        read_output_metadata(tmp_path / 'result_metadata.csv')


def test_direct_companion_does_not_look_for_another_companion(tmp_path):
    path = tmp_path / 'result_metadata.csv'
    path.write_text('field,value,type\nfunction,calibrate,string\n')
    path.with_name('result_metadata_metadata.csv').write_text(
        'field,value,type\nfunction,convert,string\n')
    assert read_output_metadata(path) == {'function': 'calibrate'}


def test_other_csv_filenames_do_not_trigger_direct_metadata_parsing(tmp_path):
    path = tmp_path / 'result_metadata_backup.csv'
    path.write_text('source_id\n1\n')
    assert read_output_metadata(path) == {}
