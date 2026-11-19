import numpy as np
import pytest

from gaiaxpy import calibrate
from gaiaxpy.config.paths import config_path
from gaiaxpy.core.config_dispatcher import CalibratorDispatcher, ErrorCorrectorDispatcher
from gaiaxpy.core.generic_variables import INV_BASIS_TYPES, RELEASES
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.continuous import dr3_mean_spectra_avro_file


def test_calibrator_dr3_config_no_sampling():
    dr3_file = dr3_mean_spectra_avro_file
    dr3_data, _, _ = (InputReader(dr3_file, calibrate, truncation=False, release=RELEASES.dr3)
                      .read())
    dr3_calibrator_file_v375wi_default = CalibratorDispatcher().build(parsed_input_data=dr3_data, sampling=None,
                                                                      bp_model='v375wi', rp_model='v142r',
                                                                      release=RELEASES.dr3,
                                                                      basis_type=INV_BASIS_TYPES.basic)
    assert dr3_calibrator_file_v375wi_default == config_path / 'xp_filter/dr3/XpFilter_v375wi_v142r.npz'


def test_calibrator_dr3_config_sampling_v375wi():
    __run_test_for_model_with_sampling_dr3(bp_model='v375wi')


def __run_test_for_model_with_sampling_dr3(bp_model):
    basis_type = INV_BASIS_TYPES.basic
    dr3 = RELEASES.dr3
    dr3_file = dr3_mean_spectra_avro_file
    dr3_data, _, _ = InputReader(dr3_file, calibrate, truncation=False, release=dr3).read()
    sampling = np.linspace(0, 60, 600)
    rp_model = 'v142r'
    files_dict = CalibratorDispatcher().build(parsed_input_data=dr3_data, sampling=sampling, bp_model=bp_model,
                                              rp_model=rp_model, release=dr3, basis_type=basis_type)
    for band in BANDS:
        for kind in ['bases', 'dispersion', 'response']:
            file = files_dict[band][kind]
            assert (file == config_path /
                    f'calibrator_config/dr3/{basis_type}/{band}_dr3_{bp_model if band == BANDS.bp else rp_model}_{kind}.npz')


def test_err_corr_dispatcher_resolve():
    dispatcher = ErrorCorrectorDispatcher()
    dr3_path, dr3_pattern = dispatcher.resolve(RELEASES.dr3)
    assert dr3_path == config_path / 'correction_tables' / RELEASES.dr3
    assert dr3_pattern == 'DIDREQ-465-{system}-correction-factors.csv'


__expected_dr3_systems = ['DR3_Stromgren', 'DR3_HstAcswfc', 'DR3_EuclidVis', 'DR3_ElsCustomW09S2', 'DR3_Iphas',
                          'DR3_StromgrenStd', 'DR3_Jkc', 'DR3_Jpas', 'DR3_JwstNircam', 'DR3_HstHugsStd',
                          'DR3_Panstarrs1', 'DR3_HipparcosTycho', 'DR3_Wfirst', 'DR3_SkyMapper', 'DR3_Sdss',
                          'DR3_Jplus', 'DR3_Gaia2', 'DR3_HstWfpc2', 'DR3_Panstarrs1Std', 'DR3_GaiaVega', 'DR3_JkcStd',
                          'DR3_HstWfc3uvis', 'DR3_Pristine', 'DR3_SdssStd']


@pytest.mark.parametrize('release,solution,length', [(RELEASES.dr3, __expected_dr3_systems, 24)])
def test_err_corr_build_systems_names(release, solution, length):
    dispatcher = ErrorCorrectorDispatcher()
    computed_systems = dispatcher.build_systems_names(release)
    assert len(computed_systems) == length
    assert set(computed_systems) == set(solution)
