import copy

import numpy as np
import pytest

from gaiaxpy import calibrate
from gaiaxpy.config.paths import config_path
from gaiaxpy.core.config_metadata import read_config_metadata
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.output_metadata import collect_output_metadata
from gaiaxpy.core.satellite import BANDS
from tests.files.continuous import dr3_mean_spectra_csv_file


def test_public_calibrate_returns_independent_metadata():
    first, _ = calibrate(dr3_mean_spectra_csv_file, save_file=False)
    second, _ = calibrate(dr3_mean_spectra_csv_file, save_file=False)
    expected = copy.deepcopy(second.attrs['gaiaxpy_metadata'])
    first.attrs['gaiaxpy_metadata']['configuration_files'][0]['metadata']['changes'][0]['description'] = 'Edited'
    assert second.attrs['gaiaxpy_metadata'] == expected
    entry = expected['configuration_files'][0]
    assert read_config_metadata(config_path / entry['file']) == entry['metadata']


def test_legacy_config_is_listed_without_invented_metadata(tmp_path, monkeypatch):
    from gaiaxpy.core import output_metadata
    monkeypatch.setattr(output_metadata, 'config_path', tmp_path)
    path = tmp_path / 'legacy.npz'
    np.savez(path, values=np.array([1., 2.]))
    result = collect_output_metadata('calibrate', RELEASES.dr3, {BANDS.bp: {'bases': path},
                                                                 BANDS.rp: {'bases': path}})
    assert result['configuration_files'] == [{'file': 'legacy.npz', 'metadata': {}}]
    assert 'input_correction' not in result


def test_malformed_metadata_is_not_silently_dropped(tmp_path, monkeypatch):
    from gaiaxpy.core import output_metadata
    monkeypatch.setattr(output_metadata, 'config_path', tmp_path)
    path = tmp_path / 'invalid.npz'
    np.savez(path, __gaiaxpy_metadata__=np.asarray('{invalid'))
    with pytest.raises(ValueError):
        collect_output_metadata('calibrate', RELEASES.dr3, path)
