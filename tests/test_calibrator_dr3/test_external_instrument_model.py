import numpy as np
import pytest

from gaiaxpy.calibrator.calibrator import _create_merge
from gaiaxpy.calibrator.external_instrument_model import ExternalInstrumentModel
from gaiaxpy.core.config import load_xpmerge_from_file, load_xpsampling_from_file
from gaiaxpy.core.config_dispatcher import CalibratorDispatcher
from gaiaxpy.core.generic_functions import parse_band
from gaiaxpy.core.generic_variables import INV_BASIS_TYPES, RELEASES
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from tests.utils.utils import assert_band_err

atol, rtol = 1e-12, 1e-12


def __get_file_for_xp(_xp, key):
    _xp = parse_band(_xp)
    _basis_type = INV_BASIS_TYPES.basic
    models = {BANDS.bp: 'v375wi', BANDS.rp: 'v142r'}
    config_files = CalibratorDispatcher().build(release=RELEASES.dr3, sampling=np.linspace(330, 1050, 60),
                                                bp_model=models[BANDS.bp], rp_model=models[BANDS.rp],
                                                basis_type=_basis_type)
    return config_files[_xp][key]


@pytest.fixture(scope='module')
def instrument_model():
    disp_files = {xp: __get_file_for_xp(xp, 'dispersion') for xp in BANDS}
    resp_files = {xp: __get_file_for_xp(xp, 'response') for xp in BANDS}
    bases_files = {xp: __get_file_for_xp(xp, 'bases') for xp in BANDS}
    _instr_model = {xp: ExternalInstrumentModel.from_config_npz(disp_files[xp], resp_files[xp], bases_files[xp]) for
                    xp in BANDS}
    yield _instr_model


@pytest.fixture(scope='module')
def sampling_grid_xp_merge():
    basis_type = INV_BASIS_TYPES.basic
    config_file = CalibratorDispatcher().build(sampling=None, bp_model='v375wi', rp_model='v142r',
                                               release=RELEASES.dr3, basis_type=basis_type)
    assert config_file.stem == 'XpFilter_v375wi_v142r'

    _sampling_grid, _xp_merge = load_xpmerge_from_file(config_file)
    yield _sampling_grid, _xp_merge


@pytest.fixture(scope='module')
def design_matrices_from_instrument_model(instrument_model, sampling_grid_xp_merge):
    _sampling_grid, _xp_merge = sampling_grid_xp_merge
    design_matrices = {xp: SampledBasisFunctions.from_external_instrument_model(_sampling_grid,
                                                                                _xp_merge,
                                                                                instrument_model, xp,
                                                                                release=RELEASES.dr3) for xp in BANDS}
    yield design_matrices


@pytest.fixture(scope='module')
def xp_merge_from_instrument_model(sampling_grid_xp_merge):
    _sampling_grid, _ = sampling_grid_xp_merge
    yield {xp: _create_merge(xp, _sampling_grid, release=RELEASES.dr3) for xp in BANDS}


@pytest.mark.parametrize('band', BANDS)
def test_band_design_matrix_from_instrument_model(band, design_matrices_from_instrument_model):
    basis_type = INV_BASIS_TYPES.basic
    config_file = CalibratorDispatcher().build(release=RELEASES.dr3, bp_model='v375wi', rp_model='v142r',
                                               sampling=None, basis_type=basis_type)
    assert config_file.stem == 'XpFilter_v375wi_v142r'

    design_matrices_from_npz = load_xpsampling_from_file(config_file)
    assert isinstance(design_matrices_from_instrument_model[band].design_matrix, np.ndarray), assert_band_err(band)
    assert isinstance(design_matrices_from_npz[band], np.ndarray), assert_band_err(band)
    assert np.allclose(design_matrices_from_instrument_model[band].design_matrix, design_matrices_from_npz[band],
                       rtol=rtol, atol=atol), assert_band_err(band)


@pytest.mark.parametrize('band', BANDS)
def test_band_merge(band, sampling_grid_xp_merge, xp_merge_from_instrument_model):
    _, xp_merge = sampling_grid_xp_merge
    assert np.allclose(xp_merge_from_instrument_model[band], xp_merge[band], rtol=rtol, atol=atol), assert_band_err(
        band)
