import importlib
from shutil import copyfile

import pandas.testing as pdt
import pytest

from gaiaxpy import PhotometricSystem, generate, load_additional_systems, remove_additional_systems
from gaiaxpy.core.custom_errors import InvalidReleaseError
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.photometric_system.config import load_config
from tests.files.continuous import dr3_with_missing_bp_csv_file
from tests.files.generator import additional_filters_dir
from tests.test_generator.test_load_additional_systems import _write_minimal_dr3_filter

ps_module = importlib.import_module('gaiaxpy.photometric_system.photometric_system')


@pytest.fixture(autouse=True)
def isolated_selection(tmp_path, monkeypatch):
    remove_additional_systems()
    monkeypatch.setattr(ps_module, '_CFG_FILE_PATH', str(tmp_path / 'selection.yaml'))
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    yield
    remove_additional_systems()


@pytest.mark.parametrize('release,extension', [(RELEASES.dr3, 'xml')])
@pytest.mark.parametrize('as_string', [False, True], ids=['path', 'str'])
def test_single_metadata_free_file(release, extension, as_string, tmp_path):
    filters = tmp_path / 'filters'
    filters.mkdir()
    if release == RELEASES.dr3:
        writer = _write_minimal_dr3_filter
    else:
        InvalidReleaseError(release)
    source = writer(filters, system_name='UserCreated', extension=extension)
    # Explicit file selection must not load neighbouring filters.
    writer(filters, system_name='Neighbour', extension=extension)
    original = {p: p.read_bytes() for p in filters.iterdir()}
    selected = str(source) if as_string else source
    assert load_additional_systems(selected) is PhotometricSystem
    assert PhotometricSystem[f'USER_{release.upper()}_UserCreated_v1'].get_bands() == ['G']
    assert not hasattr(PhotometricSystem, f'USER_{release.upper()}_Neighbour_v1')
    assert {p: p.read_bytes() for p in filters.iterdir()} == original
    config = load_config(ps_module._CFG_FILE_PATH)
    assert config['file_records'] == [{'name': 'UserCreated', 'release': release, 'version': 'v1',
                                       'filename': source.name, 'path': str(source.resolve())}]
    assert config['filters_dir'] == str(filters.resolve())
    assert ps_module.get_current_filters_path() == str(source.resolve())


@pytest.mark.parametrize('filename', ['Unsupported.gaiaxpy_dr4_v1.xml', 'Unsupported.gaiaxpy_dr3_v1.yaml',
                                      'Unsupported.gaiaxpy_dr5_v1.yaml'])
def test_invalid_explicit_file_is_rejected_format(filename, tmp_path):
    source = tmp_path / filename
    source.write_text('irrelevant content')
    with pytest.raises(ValueError, match='Additional photometric systems must be DR3 XML filter files') as error:
        load_additional_systems(source)
    assert str(source) in str(error.value)
    assert not any(s.name.startswith('USER_') for s in PhotometricSystem)


@pytest.mark.parametrize('filename', ['notes.txt', 'Unknown.yaml', 'Bad.gaiaxpy_dr4_v1.yaml.bak'])
def test_invalid_explicit_file_is_rejected_unsupported(filename, tmp_path):
    source = tmp_path / filename
    source.write_text('irrelevant content')
    with pytest.raises(ValueError, match='Unsupported additional-filter filename') as error:
        load_additional_systems(source)
    assert str(source) in str(error.value)
    assert not any(s.name.startswith('USER_') for s in PhotometricSystem)


@pytest.mark.parametrize('bad_input', ['', 'missing'])
def test_invalid_path_is_rejected(bad_input, tmp_path):
    path = '' if bad_input == '' else tmp_path / bad_input
    with pytest.raises(ValueError, match='file or directory'):
        load_additional_systems(path)


def test_nested_duplicate_reports_both_paths(tmp_path):
    filters = tmp_path / 'filters'
    nested = filters / 'nested'
    nested.mkdir(parents=True)
    first = _write_minimal_dr3_filter(filters)
    second = nested / first.name
    copyfile(first, second)
    with pytest.raises(ValueError, match='Duplicate additional-filter identity') as error:
        load_additional_systems(filters)
    assert str(first) in str(error.value)
    assert str(second) in str(error.value)


@pytest.mark.parametrize('first_name,second_name', [('Example-Filter', 'Example_Filter'), ('JKC', 'Jkc')])
def test_identifier_or_column_label_collision_is_rejected(first_name, second_name, tmp_path):
    # Use separate directories so names differing only by case remain distinct
    # on case-insensitive filesystems (such as the default macOS filesystem).
    first_dir = tmp_path / 'first'
    second_dir = tmp_path / 'second'
    first_dir.mkdir()
    second_dir.mkdir()
    first = _write_minimal_dr3_filter(first_dir, system_name=first_name)
    second = _write_minimal_dr3_filter(second_dir, system_name=second_name)
    with pytest.raises(ValueError, match='collision') as error:
        load_additional_systems(tmp_path)
    assert str(first) in str(error.value)
    assert str(second) in str(error.value)


def test_equivalent_version_labels_collide(tmp_path):
    first = _write_minimal_dr3_filter(tmp_path, version='1')
    second = _write_minimal_dr3_filter(tmp_path, version='v1')
    with pytest.raises(ValueError, match='identifier collision') as error:
        load_additional_systems(tmp_path)
    assert str(first) in str(error.value)
    assert str(second) in str(error.value)


def test_unrelated_systems_with_different_versions(tmp_path):
    _write_minimal_dr3_filter(tmp_path, system_name='First', version='v1')
    _write_minimal_dr3_filter(tmp_path, system_name='Second', version='v2')
    load_additional_systems(tmp_path)
    assert PhotometricSystem.USER_DR3_First_v1.get_bands() == ['G']
    assert PhotometricSystem.USER_DR3_Second_v2.get_bands() == ['G']


def test_successive_file_loads_replace_the_selection_and_removal_still_works(tmp_path):
    first = _write_minimal_dr3_filter(tmp_path)
    load_additional_systems(first)
    assert hasattr(PhotometricSystem, 'USER_DR3_TinyDr3_v1')
    assert 'USER_DR3_TinyDr3_v1' in PhotometricSystem.get_available_systems()
    assert remove_additional_systems() is PhotometricSystem
    assert not any(s.name.startswith('USER_') for s in PhotometricSystem)


def test_legacy_downloaded_xml_generates_the_same_photometry(tmp_path):
    source = additional_filters_dir / 'Sdss.gaiaXPy_dr3_v1.xml'
    expected_bytes = source.read_bytes()
    load_additional_systems(source)
    from_file = generate(dr3_with_missing_bp_csv_file, PhotometricSystem.USER_DR3_Sdss_v1, save_file=False)
    load_additional_systems(additional_filters_dir)
    from_directory = generate(dr3_with_missing_bp_csv_file, PhotometricSystem.USER_DR3_Sdss_v1, save_file=False)
    pdt.assert_frame_equal(from_file, from_directory)
    assert source.read_bytes() == expected_bytes


def test_empty_directory_selection_does_not_replace_previous_systems(tmp_path, capsys):
    load_additional_systems(additional_filters_dir / 'Sdss.gaiaXPy_dr3_v1.xml')
    original = PhotometricSystem.USER_DR3_Sdss_v1
    empty = tmp_path / 'empty'
    empty.mkdir()
    unrelated = empty / 'notes.txt'
    unrelated.write_text('not a filter')
    with pytest.raises(ValueError, match='No filter files'):
        load_additional_systems(empty)
    stderr = capsys.readouterr().err
    assert 'UserWarning: Ignoring files' in stderr
    assert str(unrelated.resolve()) in stderr
    assert PhotometricSystem.USER_DR3_Sdss_v1 is original
