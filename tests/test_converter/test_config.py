import unittest
from configparser import ConfigParser
from os import path

import pandas as pd

from gaiaxpy.config.paths import config_path
from gaiaxpy.converter import config

configparser = ConfigParser()
configparser.read(path.join(config_path, 'config.ini'))
config_file = path.join(config_path, configparser.get('converter', 'optimised_bases'))

columns = [
    'uniqueId',
    'dimension',
    'range',
    'normalizedRange',
    'transformedSetDimension',
    'transformationMatrix']

parsed_config = config.parse_configuration_file(config_file, columns)
loaded_config = config.load_config(config_file)  # id 7 not in the config file

not_empty_df = config.get_config(parsed_config, 57)  # id 57 in the config file
empty_df = config.get_config(parsed_config, 7)


class TestParseConfigurationFile(unittest.TestCase):

    def test_parse_configuration_file_type(self):
        self.assertIsInstance(parsed_config, pd.DataFrame)

    def test_parse_configuration_dimensions(self):
        self.assertEqual(parsed_config.shape, (2, 6))

    def test_parse_configuration_columns(self):
        self.assertEqual(list(parsed_config.columns), columns)


class TestLoadConfig(unittest.TestCase):

    def test_load_config_type(self):
        self.assertIsInstance(loaded_config, pd.DataFrame)

    def test_load_config_dimensions(self):
        self.assertEqual(loaded_config.shape, parsed_config.shape)

    def test_load_config_columns(self):
        self.assertEqual(
            loaded_config.columns.all(),
            parsed_config.columns.all())


class TestGetConfig(unittest.TestCase):

    def test_get_config_not_empty_df(self):
        self.assertEqual(not_empty_df.shape, (1, 6))
        self.assertIsInstance(not_empty_df, pd.DataFrame)
        self.assertEqual(list(not_empty_df), columns)

    def test_get_config_empty_df(self):
        self.assertEqual(empty_df.shape, (0, 6))
        self.assertIsInstance(empty_df, pd.DataFrame)
        self.assertEqual(list(empty_df), columns)
