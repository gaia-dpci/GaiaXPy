import copy
import json
from shutil import copyfile

import pandas as pd
import pytest

from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.config.paths import config_path
from gaiaxpy.core.config_metadata import read_config_metadata
from gaiaxpy.core.custom_errors import InvalidReleaseError
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.core.version import __version__
from gaiaxpy.photometric_system.photometric_system import __load_additional_systems, remove_additional_systems
from tests.files.continuous import dr3_mean_spectra_csv_file
from tests.files.paths import input_files_path


def input_frame(release):
    if release == RELEASES.dr3:
        frame = (pd.read_csv(dr3_mean_spectra_csv_file, **CSV_FLOAT_PRECISION_KWARGS)).iloc[:1].copy()
    else:
        raise InvalidReleaseError(release)
    return frame


def assert_embedded_files(metadata):
    entries = metadata['configuration_files'] + metadata['error_correction']['files']
    for entry in entries:
        assert entry['metadata'] == read_config_metadata(config_path / entry['file'])
        assert entry['metadata']
    assert json.loads(json.dumps(metadata)) == metadata


@pytest.mark.parametrize('release', RELEASES)
@pytest.mark.parametrize('input_correction', [False, True])
@pytest.mark.parametrize('error_correction', [False, True])
def test_multiple_systems_record_files_and_preserve_numbers(
        mocker, release, input_correction, error_correction):
    systems = ([PhotometricSystem.DR3_SDSS, PhotometricSystem.DR3_JKC])
    data = input_frame(release)
    data['extra'] = [42]
    data.attrs['gaiaxpy_metadata'] = {'input_only': True}
    original = copy.deepcopy(data)
    output = generate(data, systems, error_correction=error_correction, additional_columns=['extra'], save_file=False)
    metadata = output.attrs['gaiaxpy_metadata']
    assert metadata['function'] == 'generate'
    assert metadata['data_release'] == release
    assert metadata['gaiaxpy_version'] == __version__
    assert [record['system'] for record in metadata['photometric_systems']] == [s.get_system_full_label() for s in
                                                                                systems]
    correction = metadata['error_correction']
    assert correction['requested'] is error_correction
    assert correction['status'] == ('applied' if error_correction else 'disabled')
    assert {record['system'] for record in correction['systems']} == (
        {s.get_system_full_label() for s in systems} if error_correction else set())
    assert all(record['passbands'] for record in correction['systems'])
    assert metadata['standardisation'] == []
    assert len(metadata['reference_photometric_systems']) == int(error_correction)
    assert len(metadata['configuration_files']) == 2 + int(error_correction)
    assert_embedded_files(metadata)
    assert output['extra'].tolist() == [42]

    mocker.patch('gaiaxpy.generator.generator.build_generator_metadata', return_value={})
    unchanged = generate(data, systems, error_correction=error_correction, additional_columns=['extra'],
                         save_file=False)
    pd.testing.assert_frame_equal(output, unchanged)
    pd.testing.assert_frame_equal(data, original)
    assert data.attrs == original.attrs


def test_dr3_standardisation_tracks_offsets_and_colour_equations():
    systems = [PhotometricSystem.DR3_JKC_Std, PhotometricSystem.DR3_SDSS_Std]
    output = generate(input_frame(RELEASES.dr3), systems, save_file=False)
    metadata = output.attrs['gaiaxpy_metadata']
    for system in systems:
        methods = {r['method'] for r in metadata['standardisation'] if r['system'] == system.get_system_full_label()}
        assert methods == {'flux_bias', 'colour_equation'}
    assert {entry['file'] for entry in metadata['configuration_files'] if 'colour_eq_files' in entry['file']} == {
        'colour_eq_files/dr3/DR3_JkcStd_colour_eq.yaml', 'colour_eq_files/dr3/DR3_SdssStd_colour_eq.yaml'}
    assert metadata['reference_photometric_systems'] == []
    assert_embedded_files(metadata)


def test_error_table_is_recorded_as_applied():
    output = generate(input_frame(RELEASES.dr3), PhotometricSystem.DR3_Euclid_VIS, error_correction=True,
                      save_file=False)
    correction = output.attrs['gaiaxpy_metadata']['error_correction']
    assert correction['requested'] is True
    assert correction['status'] == 'applied'
    assert len(correction['files']) == 1
    assert isinstance(correction['systems'], list)
    assert set(correction['systems'][0].keys()) == {'file', 'system', 'passbands'}
    assert correction['systems'][0]['system'] == 'DR3_EuclidVis'


@pytest.fixture
def additional_system_selection():
    remove_additional_systems()  # Clear any selection left by earlier tests, so this test starts clean.
    yield
    remove_additional_systems()  # Remove what this test loaded, so it doesn’t affect later tests.


@pytest.mark.parametrize('release', RELEASES)
def test_additional_filters_include_metadata_when_available(tmp_path, release,
                                                            additional_system_selection):
    filter_dir = tmp_path / 'filters'
    filter_dir.mkdir()
    destination = filter_dir / 'Sdss.gaiaXPy_dr3_v1.xml'
    source = input_files_path.parent / 'config/additional_filters/Sdss.gaiaXPy_dr3_v1.xml'
    copyfile(source, destination)
    systems = __load_additional_systems(str(filter_dir), str(tmp_path / 'systems.yaml'))
    system = systems[f'USER_{release.upper()}_Sdss_v1']
    output = generate(input_frame(release), system, save_file=False)
    metadata = output.attrs['gaiaxpy_metadata']
    assert metadata['configuration_files'] == [{
        'file': destination.name, 'external': True, 'metadata': read_config_metadata(destination)}]
    assert metadata['configuration_files'][0]['metadata'] == {}  # XML (legacy) additional filters contain no metadata


def test_metadata_is_independent_between_calls():
    first = generate(input_frame(RELEASES.dr3), PhotometricSystem.DR3_SDSS, save_file=False)
    second = generate(input_frame(RELEASES.dr3), PhotometricSystem.DR3_SDSS, save_file=False)
    original = copy.deepcopy(second.attrs['gaiaxpy_metadata'])
    first.attrs['gaiaxpy_metadata']['configuration_files'][0]['metadata']['reference'] = 'edited'
    assert second.attrs['gaiaxpy_metadata'] == original
    assert_embedded_files(original)
