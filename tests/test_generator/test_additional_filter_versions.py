import importlib
from shutil import copyfile

import numpy as np
import pytest

from gaiaxpy import PhotometricSystem, generate, load_additional_systems, remove_additional_systems
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


def test_same_name_across_releases_and_unrelated_versions(tmp_path):
    _write_minimal_dr3_filter(tmp_path, system_name='Example', version='v1')
    _write_minimal_dr3_filter(tmp_path, system_name='Other', version='v7')
    load_additional_systems(tmp_path)
    names = {s.name for s in PhotometricSystem if s.name.startswith('USER_')}
    assert names == {'USER_DR3_Example_v1', 'USER_DR3_Other_v7'}


def test_versioned_dr3_standardised_system_keeps_flux_bias(tmp_path):
    filters = tmp_path / 'filters'
    filters.mkdir()
    source = additional_filters_dir / 'Panstarrs1Std.gaiaXPy_dr3_v1.xml'
    for version in ('v1', 'v2'):
        copyfile(source, filters / f'ExampleStd.gaiaxpy_dr3_{version}.xml')
    load_additional_systems(filters)
    systems = [PhotometricSystem.USER_DR3_ExampleStd_v1, PhotometricSystem.USER_DR3_ExampleStd_v2]
    assert all(s.value.__class__.__name__ == 'StandardisedPhotometricSystem' for s in systems)
    output = generate(dr3_with_missing_bp_csv_file, systems + [PhotometricSystem.DR3_PanSTARRS1_Std],
                      save_file=False, disable_info=True)
    for version in ('v1', 'v2'):
        for column in output:
            if column.startswith('DR3_Panstarrs1Std_'):
                equivalent = column.replace('DR3_Panstarrs1Std_', f'USER_DR3_ExampleStd_{version}_')
                np.testing.assert_allclose(output[equivalent], output[column], equal_nan=True)
    records = output.attrs['gaiaxpy_metadata']['standardisation']
    assert {r['system'] for r in records if r['system'].startswith('USER_')} == {
        'USER_DR3_ExampleStd_v1', 'USER_DR3_ExampleStd_v2'}
