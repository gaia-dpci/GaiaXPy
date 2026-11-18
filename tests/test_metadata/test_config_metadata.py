import json
from pathlib import Path

import pytest

from gaiaxpy.config.paths import config_path
from gaiaxpy.core.config_metadata import read_config_metadata, validate_config_metadata

ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILES = sorted(path for path in config_path.rglob('*')
                      if path.is_file() and path.suffix in {'.npz', '.yaml', '.yml', '.csv', '.avro'}
                      and path.name != 'config.yaml')


@pytest.fixture
def metadata():
    return {'schema_version': 1, 'version': '1', 'component_type': 'test', 'data_release': 'dr3',
            'original_filename': 'original.npz', 'description': 'Test scientific configuration.',
            'changes': [{'version': '1', 'description': 'Initial registration.'}],
            'internal_identifiers': ['test-model'], 'basis_type': 'basic'}


@pytest.mark.parametrize('path', CONFIG_FILES, ids=[str(p.relative_to(config_path)) for p in CONFIG_FILES])
def test_packaged_configuration_has_valid_embedded_metadata(path):
    metadata = read_config_metadata(path)
    assert metadata, f'Missing embedded scientific metadata: {path}'
    validate_config_metadata(metadata)


@pytest.mark.parametrize('wrong_update', [
    {'schema_version': True}, {'schema_version': 2}, {'data_release': 'dr9'}, {'version': ''},
    {'original_filename': 'folder/test.npz'}, {'changes': []}, {'basis_type': 'unknown'},
    {'internal_identifiers': 'not a list'}, {'reference': ''}
])
def test_invalid_metadata_is_rejected(wrong_update, metadata):
    with pytest.raises(ValueError):
        validate_config_metadata({**metadata, **wrong_update})


def test_missing_and_unsupported_files_raise(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_config_metadata(tmp_path / 'missing.npz')
    path = tmp_path / 'unknown.txt'
    path.write_text('text')
    with pytest.raises(ValueError, match='Unsupported'):
        read_config_metadata(path)


def test_malformed_metadata_does_not_look_like_legacy_file(tmp_path):
    path = tmp_path / 'bad.csv'
    path.write_text('# gaiaxpy_metadata: {broken}\nx,y\n1,2\n')
    with pytest.raises(ValueError):
        read_config_metadata(path)


def test_duplicate_metadata_header_is_rejected(tmp_path, metadata):
    path = tmp_path / 'bad.csv'
    line = '# gaiaxpy_metadata: ' + json.dumps(metadata) + '\n'
    path.write_text(line + line + 'x,y\n1,2\n')
    with pytest.raises(ValueError, match='Duplicate'):
        read_config_metadata(path)


@pytest.mark.parametrize('additional_filter', [False, True])
def test_complete_metadata_is_valid_in_both_modes(metadata, additional_filter):
    validate_config_metadata(metadata, additional_filter=additional_filter)


def test_minimal_metadata_requires_additional_filter_option():
    metadata = {'version': '1'}
    with pytest.raises(ValueError, match='schema_version'):
        validate_config_metadata(metadata)
    validate_config_metadata(metadata, additional_filter=True)


@pytest.mark.parametrize('field', ['component_type', 'data_release', 'original_filename', 'description', 'changes'])
def test_additional_fields_are_optional_but_packaged_fields_are_required(metadata, field):
    metadata.pop(field)
    validate_config_metadata(metadata, additional_filter=True)
    with pytest.raises(ValueError):
        validate_config_metadata(metadata)


@pytest.mark.parametrize('additional_filter', [False, True])
@pytest.mark.parametrize('wrong_update', [
    {'schema_version': True}, {'schema_version': 2}, {'version': ''}, {'version': 1},
    {'data_release': 'dr9'}, {'description': 3}, {'original_filename': 'folder/test.yaml'},
    {'changes': 'history'}, {'changes': [None]}, {'changes': [{'version': 1}]},
    {'basis_type': 'unknown'}, {'internal_identifiers': 'not a list'}, {'reference': ''},
    {'custom': float('nan')}, {'custom': object()}
])
def test_supplied_fields_are_validated_in_both_modes(metadata, wrong_update, additional_filter):
    with pytest.raises(ValueError):
        validate_config_metadata({**metadata, **wrong_update}, additional_filter=additional_filter)


@pytest.mark.parametrize('changes', [[], [{}], [{'version': 'older'}], [{'description': 'Optional history'}]])
def test_additional_history_does_not_require_complete_packaged_history(changes):
    validate_config_metadata({'version': '1', 'changes': changes}, additional_filter=True)
