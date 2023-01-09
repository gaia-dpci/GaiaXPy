import unittest
from configparser import ConfigParser
from os import path

import numpy as np
from numpy import ndarray

from gaiaxpy.calibrator.calibrator import _create_merge
from gaiaxpy.calibrator.external_instrument_model import ExternalInstrumentModel
from gaiaxpy.config.paths import config_path
from gaiaxpy.core import satellite
from gaiaxpy.core.config import _load_xpmerge_from_xml, _load_xpsampling_from_xml
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))

rel_tol = 1e-6
abs_tol = 1e-4

label = 'calibrator'
models = {BANDS.bp: 'v375wi', BANDS.rp: 'v142r'}


def get_file_for_xp(xp, key):
    model = models[xp]
    file_name = config_parser.get(label, key)
    return f"{config_path}/{file_name.replace('xp', xp).replace('model', model)}".format(key)


# The design matrices for the default grid are loaded to be used as reference for the test.
design_matrices_from_csv = _load_xpsampling_from_xml()
sampling_grid, xp_merge = _load_xpmerge_from_xml()

xp_merge_from_instrument_model = {}
design_matrices_from_instrument_model = {}
for xp in satellite.BANDS:
    instr_model = ExternalInstrumentModel.from_config_csv(get_file_for_xp(xp, 'dispersion'),
                                                          get_file_for_xp(xp, 'response'),
                                                          get_file_for_xp(xp, 'bases'))
    xp_merge_from_instrument_model[xp] = _create_merge(xp, sampling_grid)
    design_matrices_from_instrument_model[xp] = SampledBasisFunctions.from_external_instrument_model(sampling_grid,
                                                                                                     xp_merge[xp],
                                                                                                     instr_model)


class TestDesignMatrix(unittest.TestCase):

    def test_bp_design_matrix_from_instrument_model_types(self):
        self.assertIsInstance(
            design_matrices_from_instrument_model[BANDS.bp].design_matrix, ndarray)
        self.assertIsInstance(design_matrices_from_csv[BANDS.bp], ndarray)

    def test_bp_design_matrix_from_instrument_model(self):
        self.assertTrue(np.allclose(design_matrices_from_instrument_model[BANDS.bp].design_matrix,
                                    design_matrices_from_csv[BANDS.bp], rel_tol, abs_tol))

    def test_rp_design_matrix_from_instrument_model_types(self):
        self.assertIsInstance(
            design_matrices_from_instrument_model[BANDS.rp].design_matrix, ndarray)
        self.assertIsInstance(design_matrices_from_csv[BANDS.rp], ndarray)

    def test_rp_design_matrix_from_instrument_model(self):
        self.assertTrue(np.allclose(design_matrices_from_instrument_model[BANDS.rp].design_matrix,
                                    design_matrices_from_csv[BANDS.rp], rel_tol, abs_tol))


class TestMerge(unittest.TestCase):

    def test_bp_merge(self):
        self.assertTrue(np.allclose(xp_merge_from_instrument_model[BANDS.bp], xp_merge[BANDS.bp], rel_tol, abs_tol))

    def test_rp_merge(self):
        self.assertTrue(np.allclose(xp_merge_from_instrument_model[BANDS.rp], xp_merge[BANDS.rp], rel_tol, abs_tol))
