'''
import unittest
import numpy as np
from os import path
from configparser import ConfigParser
from numpy import ndarray
from gaiaxpy.config import config_path
from gaiaxpy.simulator import get_file, XpInstrumentModel

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))
model_config_file = path.join(config_path, config_parser.get('simulator', 'model'))

bp_model='v375wi'; rp_model='v142r'
file_name = get_file(model_config_file, bp_model, rp_model)
file = open(file_name)
model_dict = {}
for band in ['bp', 'rp']:
    # Wavelength
    wl = np.fromstring(file.readline(), sep=",")
    # Kernel
    kernel_dimension = np.fromstring(file.readline(), sep=",", dtype='int')
    kernel = np.zeros(shape=(kernel_dimension[0], kernel_dimension[1]))
    for i in range(kernel_dimension[0]):
        kernel[i] = np.fromstring(file.readline(), sep=",")
    # Kernel errors
    kernel_error_dimension = np.fromstring(file.readline(), sep=",", dtype='int')
    sampled_kernel_error = np.zeros(shape=(kernel_error_dimension[0], kernel_error_dimension[1]))
    for i in range(kernel_error_dimension[0]):
        sampled_kernel_error[i] = np.fromstring(file.readline(), sep=",")
    # Pseudo inverse of design matrix
    dm_dimension = np.fromstring(file.readline(), sep=",", dtype='int')
    dm = np.zeros(shape=(dm_dimension[0], dm_dimension[1]))
    for i in range(dm_dimension[0]):
        dm[i] = np.fromstring(file.readline(), sep=",")
    model = XpInstrumentModel(wl, kernel, sampled_kernel_error, dm)
    model_dict[band] = model

class TestXpInstrumentModel(unittest.TestCase):

    def test_xp_instrument_model_init(self):
        for band in ['bp', 'rp']:
            self.assertIsInstance(model_dict[band], XpInstrumentModel)

    def test_getters(self):
        for band in ['bp', 'rp']:
            self.assertIsInstance(model_dict[band].get_wl(), ndarray)
            self.assertIsInstance(model_dict[band].get_kernel(), ndarray)
            self.assertIsInstance(model_dict[band].get_sampled_kernel_error(), ndarray)
            self.assertIsInstance(model_dict[band].get_design_matrix_pseudo_inverse(), ndarray)
            # Kernel is nested array
            self.assertIsInstance(model_dict[band].get_kernel()[0], ndarray)
            self.assertIsInstance(model_dict[band].get_sampled_kernel_error()[0], ndarray)
            self.assertIsInstance(model_dict[band].get_design_matrix_pseudo_inverse()[0], ndarray)
'''
