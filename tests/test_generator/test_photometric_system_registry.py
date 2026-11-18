import importlib
import pickle
from types import ModuleType

import pytest

from gaiaxpy import PhotometricSystem, generate, load_additional_systems, remove_additional_systems
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


def test_imports_and_return_values_keep_the_same_registry():
    other_module = ModuleType('registry_consumer')
    exec('from gaiaxpy import PhotometricSystem', other_module.__dict__)
    original = PhotometricSystem
    builtin = PhotometricSystem.DR3_SDSS
    assert load_additional_systems(additional_filters_dir) is original
    assert other_module.PhotometricSystem is original
    assert other_module.PhotometricSystem.USER_DR3_Sdss_v1 is original.USER_DR3_Sdss_v1
    assert PhotometricSystem.DR3_SDSS is builtin
    assert remove_additional_systems() is original
    assert PhotometricSystem.DR3_SDSS is builtin
    assert not hasattr(other_module.PhotometricSystem, 'USER_DR3_Sdss_v1')


def test_enum_style_access_and_type_checks():
    system = PhotometricSystem.DR3_SDSS
    assert PhotometricSystem['DR3_SDSS'] is system
    assert PhotometricSystem(system.value) is system
    assert isinstance(system, PhotometricSystem)
    assert system in PhotometricSystem
    assert 'unknown' not in PhotometricSystem
    assert len(PhotometricSystem) == len(list(PhotometricSystem))
    assert list(reversed(PhotometricSystem)) == list(PhotometricSystem)[::-1]
    assert PhotometricSystem.__members__['DR3_SDSS'] is system
    assert str(system) == 'PhotometricSystem.DR3_SDSS'
    assert ps_module.get_available_systems() == PhotometricSystem.get_available_systems()
    with pytest.raises(TypeError):
        PhotometricSystem.__members__['new'] = system
    with pytest.raises(AttributeError):
        PhotometricSystem.DR3_SDSS = object()
    with pytest.raises(AttributeError):
        _ = PhotometricSystem.unknown
    with pytest.raises(KeyError):
        _ = PhotometricSystem['unknown']
    with pytest.raises(ValueError):
        PhotometricSystem(object())


def test_grouped_system_names_support_case_insensitive_lookup():
    available = PhotometricSystem.get_available_systems()
    assert isinstance(available, str)
    assert available[:4] == 'DR3:'
    assert available['dr3'] == [member.name for member in PhotometricSystem if member.name.startswith('DR3_')]
    assert available['additional systems'] == []
    with pytest.raises(KeyError):
        available['dr4']

    load_additional_systems(additional_filters_dir)
    available = PhotometricSystem.get_available_systems()
    additional = [member.name for member in PhotometricSystem if member.name.startswith('USER_')]
    assert additional
    assert available['Additional systems'] == additional
    available['ADDITIONAL SYSTEMS'].clear()
    assert available['additional systems'] == additional
    assert PhotometricSystem.get_available_systems(grouped=False).split(', ') == (available['DR3'] + additional)


def test_ipython_completion():
    completers = pytest.importorskip('IPython.core.completer')
    completer = completers.IPCompleter(namespace={'PhotometricSystem': PhotometricSystem}, use_jedi=False)
    assert 'PhotometricSystem.DR3_SDSS' in completer.attr_matches('PhotometricSystem.DR3_S')
    load_additional_systems(additional_filters_dir)
    assert 'PhotometricSystem.USER_DR3_Sdss_v1' in completer.attr_matches('PhotometricSystem.USER_DR3_S')
    remove_additional_systems()
    assert not completer.attr_matches('PhotometricSystem.USER_')


def test_refusing_replacement_keeps_selection(monkeypatch, tmp_path):
    load_additional_systems(additional_filters_dir)
    retained = PhotometricSystem.USER_DR3_Sdss_v1
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    assert load_additional_systems(tmp_path / 'does-not-exist') is PhotometricSystem
    assert PhotometricSystem.USER_DR3_Sdss_v1 is retained


def test_registry_and_builtin_pickle_preserve_identity():
    assert pickle.loads(pickle.dumps(PhotometricSystem)) is PhotometricSystem
    system = PhotometricSystem.DR3_SDSS
    assert pickle.loads(pickle.dumps(system)) is system


@pytest.mark.parametrize('selection, invalid_entries', [
    ('DR4_DES_Std', "'DR4_DES_Std'"),
    (['DR4_DES_Std'], "'DR4_DES_Std'"),
    (42, 'int')
])
def test_generation_reports_invalid_system_entries(selection, invalid_entries, mocker):
    reader = mocker.patch('gaiaxpy.generator.generator.InputReader')
    with pytest.raises(TypeError) as error:
        generate(None, selection, save_file=False)
    assert str(error.value) == ('photometric_system must be a PhotometricSystem member or a list of members. '
                                f'Invalid entries: {invalid_entries}.')
    reader.assert_not_called()


@pytest.mark.parametrize('as_list', [False, True], ids=['single', 'list'])
@pytest.mark.parametrize('restore_pickle', [False, True], ids=['stored', 'unpickled'])
def test_generation_rejects_removed_member(as_list, restore_pickle, mocker):
    load_additional_systems(additional_filters_dir)
    system = PhotometricSystem.USER_DR3_Sdss_v1
    saved = pickle.dumps(system)
    remove_additional_systems()
    if restore_pickle:
        system = pickle.loads(saved)
    assert not isinstance(system, PhotometricSystem)
    reader = mocker.patch('gaiaxpy.generator.generator.InputReader')
    selection = [PhotometricSystem.DR3_SDSS, system] if as_list else system
    with pytest.raises(ValueError, match='USER_DR3_Sdss_v1.*not currently loaded'):
        generate(dr3_with_missing_bp_csv_file, selection, save_file=False)
    reader.assert_not_called()


def test_generation_keeps_current_member_after_failed_or_declined_replacement(monkeypatch, tmp_path):
    load_additional_systems(additional_filters_dir / 'Sdss.gaiaXPy_dr3_v1.xml')
    current = PhotometricSystem.USER_DR3_Sdss_v1
    with pytest.raises(ValueError):
        load_additional_systems(tmp_path / 'missing')
    assert current in PhotometricSystem
    assert not generate(dr3_with_missing_bp_csv_file, current, save_file=False).empty
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    load_additional_systems(tmp_path / 'missing')
    assert current in PhotometricSystem
    assert not generate(dr3_with_missing_bp_csv_file, current, save_file=False).empty


def test_builtin_generation_survives_additional_removal():
    builtin = PhotometricSystem.DR3_SDSS
    load_additional_systems(additional_filters_dir)
    remove_additional_systems()
    assert PhotometricSystem.DR3_SDSS is builtin
    assert isinstance(builtin, PhotometricSystem)
    assert not generate(dr3_with_missing_bp_csv_file, builtin, save_file=False).empty
