import copy
import json
import shutil

import numpy as np
import pandas as pd
import pytest

from gaiaxpy import convert
from gaiaxpy.config.paths import config_path
from gaiaxpy.converter.converter import _convert
from gaiaxpy.core.config_metadata import read_config_metadata
from gaiaxpy.core.custom_errors import InvalidReleaseError
from gaiaxpy.core.generic_variables import RELEASES, VALID_EXTENSIONS
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.core.version import __version__
from gaiaxpy.output import read_output_metadata
from tests.files.continuous import dr3_mean_spectra_csv_file

CONFIG_FILES = {
    RELEASES.dr3: 'converter_config/dr3/OptimisedCalibratedBases_BpId32_RpId37_withNormalisation.npz'
}


@pytest.mark.parametrize('release', RELEASES)
@pytest.mark.parametrize('custom_sampling', [False, True])
def test_converter_metadata_preserves_results_and_input(
        mocker, release, custom_sampling):
    if release == RELEASES.dr3:
        data = (pd.read_csv(dr3_mean_spectra_csv_file, **CSV_FLOAT_PRECISION_KWARGS)).iloc[:1].copy()
    else:
        raise InvalidReleaseError(release)
    data.attrs['gaiaxpy_metadata'] = {'input_only': True}
    original = copy.deepcopy(data)
    options = {'sampling': np.linspace(0, 60, 5)} if custom_sampling else {}
    output, sampling = _convert(data, save_file=False, disable_info=True, **options)
    metadata = output.attrs['gaiaxpy_metadata']
    assert metadata['function'] == 'convert'
    assert metadata['schema_version'] == 1
    assert metadata['gaiaxpy_version'] == __version__
    assert metadata['data_release'] == release
    assert 'basis_type' not in metadata  # No inverse-basis selection in convert.
    assert metadata['configuration_files'] == [{
        'file': CONFIG_FILES[release], 'metadata': read_config_metadata(config_path / CONFIG_FILES[release])}]
    assert json.loads(json.dumps(metadata)) == metadata

    mocker.patch('gaiaxpy.converter.converter.collect_output_metadata', return_value={})
    unchanged, unchanged_sampling = _convert(data, save_file=False, disable_info=True, **options)
    np.testing.assert_array_equal(sampling, unchanged_sampling)
    assert list(output.columns) == list(unchanged.columns)
    for column in output:
        for actual, expected in zip(output[column], unchanged[column]):
            np.testing.assert_array_equal(actual, expected)
    assert output.attrs['data_type'] is unchanged.attrs['data_type']
    pd.testing.assert_frame_equal(data, original)
    assert data.attrs == original.attrs


@pytest.mark.parametrize('release', RELEASES)
@pytest.mark.parametrize('extension', VALID_EXTENSIONS)
def test_public_converter_saves_the_returned_metadata(tmp_path, release, extension):
    path = dr3_mean_spectra_csv_file
    output, _ = convert(path, sampling=np.linspace(0, 60, 5), output_path=tmp_path,
                        output_file='converted', output_format=extension, with_correlation=True)
    assert read_output_metadata(tmp_path / f'converted.{extension}') == output.attrs['gaiaxpy_metadata']


def test_converter_metadata_is_independent_between_calls():
    first, _ = convert(dr3_mean_spectra_csv_file, sampling=np.linspace(0, 60, 5), save_file=False)
    second, _ = convert(dr3_mean_spectra_csv_file, sampling=np.linspace(0, 60, 5), save_file=False)
    original = copy.deepcopy(second.attrs['gaiaxpy_metadata'])
    first.attrs['gaiaxpy_metadata']['configuration_files'][0]['metadata']['version'] = 'changed'
    assert second.attrs['gaiaxpy_metadata'] == original
    assert read_config_metadata(config_path / CONFIG_FILES[RELEASES.dr3]) == original['configuration_files'][0][
        'metadata']


def test_external_converter_config_records_the_actual_file(tmp_path):
    path = tmp_path / 'custom_bases.npz'
    shutil.copyfile(config_path / CONFIG_FILES[RELEASES.dr3], path)
    output, _ = _convert(dr3_mean_spectra_csv_file, config_file=path, sampling=np.linspace(0, 60, 5),
                         save_file=False, disable_info=True)
    assert output.attrs['gaiaxpy_metadata']['configuration_files'] == [{
        'file': 'custom_bases.npz', 'external': True, 'metadata': read_config_metadata(path)}]


def test_external_legacy_npz_is_recorded_without_invented_metadata(tmp_path):
    path = tmp_path / 'legacy_bases.npz'
    with np.load(config_path / CONFIG_FILES[RELEASES.dr3], allow_pickle=False) as data:
        np.savez(path, **{key: data[key] for key in data.files if key != '__gaiaxpy_metadata__'})
    output, _ = _convert(dr3_mean_spectra_csv_file, config_file=path, sampling=np.linspace(0, 60, 5),
                         save_file=False, disable_info=True)
    assert output.attrs['gaiaxpy_metadata']['configuration_files'] == [{
        'file': 'legacy_bases.npz', 'external': True, 'metadata': {}}]
