"""Trace each generated additional-system column to its selected filter file."""
import importlib
import json
from copy import deepcopy
from hashlib import sha256
from shutil import copyfile

import pandas as pd
import pytest

from gaiaxpy import PhotometricSystem, generate, load_additional_systems, remove_additional_systems
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.version import __version__
from gaiaxpy.output import read_output_metadata
from tests.files.continuous import dr3_with_missing_bp_csv_file
from tests.files.generator import additional_filters_dir

ps_module = importlib.import_module('gaiaxpy.photometric_system.photometric_system')


@pytest.fixture(autouse=True)
def isolated_selection(tmp_path, monkeypatch):
    remove_additional_systems()
    monkeypatch.setattr(ps_module, '_CFG_FILE_PATH', str(tmp_path / 'selection.yaml'))
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    yield
    remove_additional_systems()


@pytest.fixture(params=['legacy_xml'])
def selection(request, tmp_path):
    release = RELEASES.dr3
    directory = tmp_path / 'filters'
    directory.mkdir()
    nested = directory / 'nested'
    nested.mkdir()
    source = (additional_filters_dir / 'Panstarrs1Std.gaiaXPy_dr3_v1.xml')
    paths, scientific = {}, {}
    for version in ('v1', 'v2', 'v9'):
        name = 'UnusedStd' if version == 'v9' else 'ExampleStd'
        path = (nested if version == 'v2' else directory) / f'{name}.gaiaxpy_{release}_{version}.{source.suffix[1:]}'
        copyfile(source, path)
        metadata = {}
        paths[version], scientific[version] = path, metadata
    load_additional_systems(directory)
    # Deliberately request a different order from discovery and leave v9 unused.
    systems = [PhotometricSystem[f'USER_{release.upper()}_ExampleStd_{version}'] for version in ('v2', 'v1')]
    data = (pd.read_csv(dr3_with_missing_bp_csv_file)).iloc[:2].copy()
    return release, paths, scientific, systems, data


def run_generate(selection, **kwargs):
    release, _, _, systems, data = selection
    return generate(data, systems, release=release, disable_info=True, **kwargs)


def assert_traceability(output, metadata, selection):
    release, paths, scientific, systems, _ = selection
    assert metadata['gaiaxpy_version'] == __version__
    records = metadata['photometric_systems']
    assert [record['system'] for record in records] == [system.get_system_full_label() for system in systems]
    mapped_columns = []
    for record, version in zip(records, ('v2', 'v1'), strict=True):
        path = paths[version]
        assert record['name'] == 'ExampleStd'
        assert record['data_release'] == release
        assert record['version'] == (version[1:] if scientific[version] else version)
        assert record['version_source'] == ('metadata' if scientific[version] else 'filename')
        assert record['filename_version'] == version
        assert record['file'] == path.name
        assert record['sha256'] == sha256(path.read_bytes()).hexdigest()
        assert record['columns'] == [column for column in output if column.startswith(record['system'] + '_')]
        assert record['columns']
        mapped_columns.extend(record['columns'])
        file_record = next(entry for entry in metadata['configuration_files'] if entry['file'] == record['file'])
        assert file_record['external'] is True
        assert file_record['metadata'] == scientific[version]
    assert len(mapped_columns) == len(set(mapped_columns))
    assert set(mapped_columns) == set(output.columns) - {'source_id'}
    assert not any('Unused' in record['file'] for record in metadata['configuration_files'])
    assert str(paths['v1'].parent) not in json.dumps(metadata)


def test_dataframe_records_only_used_filters_and_all_generated_columns(selection):
    _, paths, _, _, _ = selection
    before = {path: path.read_bytes() for path in paths.values()}
    output = run_generate(selection, save_file=False)
    assert_traceability(output, output.attrs['gaiaxpy_metadata'], selection)
    assert {path: path.read_bytes() for path in paths.values()} == before
    snapshot = deepcopy(output.attrs['gaiaxpy_metadata'])
    again = run_generate(selection, save_file=False)
    output.attrs['gaiaxpy_metadata']['photometric_systems'][0]['columns'].clear()
    assert again.attrs['gaiaxpy_metadata'] == snapshot


@pytest.mark.parametrize('output_format', ['csv', 'ecsv', 'fits', 'xml', 'avro'])
def test_saved_formats_preserve_complete_additional_filter_traceability(selection, output_format, tmp_path):
    output = run_generate(selection, output_path=tmp_path, output_file='photometry', output_format=output_format)
    metadata = read_output_metadata(tmp_path / f'photometry.{output_format}')
    assert metadata == output.attrs['gaiaxpy_metadata']
    assert_traceability(output, metadata, selection)
    if output_format == 'csv':
        assert (tmp_path / 'photometry_metadata.csv').is_file()
        assert list(pd.read_csv(tmp_path / 'photometry.csv').columns) == list(output.columns)
    remove_additional_systems()
    selection[1]['v1'].parent.rename(tmp_path / 'unavailable-filters')
    assert read_output_metadata(tmp_path / f'photometry.{output_format}') == metadata


def test_replacing_selection_rejects_old_member_and_reports_current_filter(selection):
    release, paths, _, systems, data = selection
    previous = systems[1]
    load_additional_systems(paths['v2'])
    assert not hasattr(PhotometricSystem, previous.name)
    with pytest.raises(ValueError, match='not currently loaded'):
        generate(data, previous, save_file=False, release=release, disable_info=True)
    current = PhotometricSystem[systems[0].name]
    output = generate(data, current, save_file=False, release=release, disable_info=True)
    record, = output.attrs['gaiaxpy_metadata']['photometric_systems']
    assert record['system'] == current.get_system_full_label()
    assert record['filename_version'] == 'v2'
    assert record['file'] == paths['v2'].name
    assert record['sha256'] == sha256(paths['v2'].read_bytes()).hexdigest()


def test_builtin_column_names_and_records_are_unchanged():
    data = pd.read_csv(dr3_with_missing_bp_csv_file).iloc[:1]
    output = generate(data, PhotometricSystem.DR3_SDSS, save_file=False, disable_info=True)
    record, = output.attrs['gaiaxpy_metadata']['photometric_systems']
    assert record == {'system': 'DR3_Sdss', 'file': 'filters/dr3/XpFilter_Sdss_v375wi_v142r.yaml'}
    assert all(column == 'source_id' or column.startswith('DR3_Sdss_') for column in output)
