from configparser import ConfigParser
from os.path import join

import numpy as np
import pytest
from gaiaxpy.calibrator.calibrator import __create_merge
from gaiaxpy.calibrator.external_instrument_model import ExternalInstrumentModel
from gaiaxpy.config.paths import config_path, config_ini_file
from gaiaxpy.core.config import load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from numpy import ndarray

from tests.utils.utils import assert_band_err

rtol = 1e-6
atol = 1e-4


def get_file_for_xp(_xp, key):
    label = 'calibrator'
    models = {BANDS.bp: 'v375wi', BANDS.rp: 'v142r'}
    model = models[_xp]
    config_parser = ConfigParser()
    config_parser.read(config_ini_file)
    file_name = config_parser.get(label, key)
    return join(config_path, file_name.replace('xp', _xp).replace('model', model).format(key))


@pytest.fixture(scope='module')
def instrument_model():
    _instr_model = {xp: ExternalInstrumentModel.from_config_csv(get_file_for_xp(xp, 'dispersion'),
                                                                get_file_for_xp(xp, 'response'),
                                                                get_file_for_xp(xp, 'bases')) for xp in BANDS}
    yield _instr_model


@pytest.fixture(scope='module')
def sampling_grid_xp_merge():
    _sampling_grid, _xp_merge = load_xpmerge_from_xml()
    yield _sampling_grid, _xp_merge


@pytest.fixture(scope='module')
def design_matrices_from_instrument_model(instrument_model, sampling_grid_xp_merge):
    _sampling_grid, _xp_merge = sampling_grid_xp_merge
    design_matrices = {xp: SampledBasisFunctions.from_external_instrument_model(_sampling_grid,
                                                                                _xp_merge[xp],
                                                                                instrument_model[xp]) for xp in BANDS}
    yield design_matrices


@pytest.fixture(scope='module')
def xp_merge_from_instrument_model(sampling_grid_xp_merge):
    _sampling_grid, _ = sampling_grid_xp_merge
    yield {xp: __create_merge(xp, _sampling_grid) for xp in BANDS}


@pytest.mark.parametrize('band', BANDS)
def test_band_design_matrix_from_instrument_model(band, design_matrices_from_instrument_model):
    design_matrices_from_csv = load_xpsampling_from_xml()
    assert isinstance(design_matrices_from_instrument_model[band].design_matrix, ndarray), assert_band_err(band)
    assert isinstance(design_matrices_from_csv[band], ndarray), assert_band_err(band)
    assert np.allclose(design_matrices_from_instrument_model[band].design_matrix, design_matrices_from_csv[band],
                       rtol=rtol, atol=atol), assert_band_err(band)


@pytest.mark.parametrize('band', BANDS)
def test_band_merge(band, sampling_grid_xp_merge, xp_merge_from_instrument_model):
    _, xp_merge = sampling_grid_xp_merge
    assert np.allclose(xp_merge_from_instrument_model[band], xp_merge[band], rtol=rtol, atol=atol), assert_band_err(
        band)
