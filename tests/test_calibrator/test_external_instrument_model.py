import unittest
from configparser import ConfigParser
from os.path import join

import numpy as np
from numpy import ndarray

from gaiaxpy.calibrator.calibrator import __create_merge
from gaiaxpy.calibrator.external_instrument_model import ExternalInstrumentModel
from gaiaxpy.config.paths import config_path, config_ini_file
from gaiaxpy.core import satellite
from gaiaxpy.core.config import load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from tests.utils.utils import assert_band_err

config_parser = ConfigParser()
config_parser.read(config_ini_file)

rtol = 1e-6
atol = 1e-4

label = 'calibrator'
models = {BANDS.bp: 'v375wi', BANDS.rp: 'v142r'}


def get_file_for_xp(_xp, key):
    model = models[_xp]
    file_name = config_parser.get(label, key)
    return join(config_path, file_name.replace('xp', _xp).replace('model', model).format(key))


# The design matrices for the default grid are loaded to be used as reference for the test.
design_matrices_from_csv = load_xpsampling_from_xml()
sampling_grid, xp_merge = load_xpmerge_from_xml()

xp_merge_from_instrument_model = {}
design_matrices_from_instrument_model = {}
for xp in satellite.BANDS:
    instr_model = ExternalInstrumentModel.from_config_csv(get_file_for_xp(xp, 'dispersion'),
                                                          get_file_for_xp(xp, 'response'),
                                                          get_file_for_xp(xp, 'bases'))
    xp_merge_from_instrument_model[xp] = __create_merge(xp, sampling_grid)
    design_matrices_from_instrument_model[xp] = SampledBasisFunctions.from_external_instrument_model(sampling_grid,
                                                                                                     xp_merge[xp],
                                                                                                     instr_model)


class TestExternalInstrument(unittest.TestCase):

    def test_band_design_matrix_from_instrument_model(self):
        instance = ndarray
        for band in BANDS:
            self.assertIsInstance(design_matrices_from_instrument_model[band].design_matrix, instance,
                                  msg=assert_band_err(band))
            self.assertIsInstance(design_matrices_from_csv[band], instance, msg=assert_band_err(band))
            self.assertTrue(np.allclose(design_matrices_from_instrument_model[band].design_matrix,
                                        design_matrices_from_csv[band], rtol=rtol, atol=atol),
                            msg=assert_band_err(band))

    def test_band_merge(self):
        for band in BANDS:
            self.assertTrue(np.allclose(xp_merge_from_instrument_model[band], xp_merge[band], rtol=rtol, atol=atol),
                            msg=assert_band_err(band))
