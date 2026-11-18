import numpy as np
import pytest

from gaiaxpy.calibrator.calibrator import _calibrate
from gaiaxpy.config.paths import config_path
from gaiaxpy.core.config_dispatcher import CalibratorDispatcher
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.satellite import BANDS
from tests.files.continuous import dr3_mean_spectra_csv_file


@pytest.mark.parametrize('name', ['bp_model', 'rp_model'])
def test_calibrate_rejects_removed_model_arguments(name):
    with pytest.raises(TypeError, match=f"unexpected keyword argument '{name}'"):
        _calibrate(dr3_mean_spectra_csv_file, save_file=False, **{name: None})


@pytest.mark.parametrize('release,basis_type,custom_sampling,bp_model,rp_model', [
    (RELEASES.dr3, 'basic', False, 'v375wi', 'v142r'),
    (RELEASES.dr3, 'basic', True, 'v375wi', 'v142r')
])
def test_calibrate_selects_configured_models(mocker, release, basis_type,
                                             custom_sampling, bp_model, rp_model):
    build = mocker.spy(CalibratorDispatcher, 'build')
    input_file = dr3_mean_spectra_csv_file if release == RELEASES.dr3 else None
    if not input_file:
        raise ValueError('Input file not specified')
    sampling = np.array([400., 600., 800.]) if custom_sampling else None
    output, actual_sampling = _calibrate(input_file, sampling=sampling, basis_type=basis_type, save_file=False)

    assert not output.empty
    for band in BANDS:
        assert f'{band}_model' not in build.call_args.kwargs
    assert build.call_args.kwargs['release'] == release
    files = build.spy_return
    if not custom_sampling:
        assert files == config_path / f'xp_filter/{release}/XpFilter_{bp_model}_{rp_model}.npz'
    else:
        np.testing.assert_array_equal(actual_sampling, sampling)
        for band, model in [(BANDS.bp, bp_model), (BANDS.rp, rp_model)]:
            for kind in ['bases', 'dispersion', 'response']:
                filename = f'{band}_{release}_{model}_{kind}.npz'
                assert files[band][kind] == config_path / f'calibrator_config/{release}/{basis_type}/{filename}'
