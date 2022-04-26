import unittest
from os import path
from configparser import ConfigParser
from gaiaxpy.config import config_path
from gaiaxpy.simulator import get_file, load_config, _load_model_from_hdf
from gaiaxpy.simulator.xp_instrument_model import XpInstrumentModel
from gaiaxpy.config import config_path
from gaiaxpy.core.satellite import BANDS

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))
model_config_file = path.join(config_path, config_parser.get('simulator', 'model'))


class TestConfig(unittest.TestCase):

    def test_load_model_from_hdf(self):
        loaded_config = _load_model_from_hdf(model_config_file)
        self.assertIsInstance(loaded_config, dict)
        self.assertEqual(set(loaded_config.keys()), {BANDS.bp, BANDS.rp})
        self.assertIsInstance(loaded_config[BANDS.bp], XpInstrumentModel)
        self.assertIsInstance(loaded_config[BANDS.rp], XpInstrumentModel)

    def test_load_config(self):
        loaded_config = load_config(model_config_file)
        self.assertIsInstance(loaded_config, dict)
        self.assertEqual(set(loaded_config.keys()), {BANDS.bp, BANDS.rp})
        self.assertIsInstance(loaded_config[BANDS.bp], XpInstrumentModel)
        self.assertIsInstance(loaded_config[BANDS.rp], XpInstrumentModel)

    def test_get_file(self):
        bp_model='v375wi'; rp_model='v142r'
        filename = get_file(model_config_file, bp_model, rp_model)
        self.assertIsInstance(filename, str)
        self.assertEqual(filename, path.join(config_path, f'MiogLiteModel_1nmX240_V3_{bp_model}{rp_model}.csv'))
