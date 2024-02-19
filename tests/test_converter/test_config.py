import unittest

import pandas as pd

from gaiaxpy.config.paths import hermite_bases_file
from gaiaxpy.converter.config import get_unique_id, parse_config

columns = ['dimension', 'range', 'normalizedRange', 'uniqueId', 'transformedSetDimension', 'transformationMatrix']

bases_config = parse_config(hermite_bases_file)  # id 7 not in the config file
bands_config = bases_config.hermiteFunction

bp_config = bands_config.bpConfig
rp_config = bands_config.rpConfig
bp_config_dict = {field: getattr(bp_config, field) for field in bp_config._fields}
rp_config_dict = {field: getattr(rp_config, field) for field in rp_config._fields}

parsed_config = pd.DataFrame([bp_config_dict, rp_config_dict])

not_empty_df = get_unique_id(parsed_config, 57)  # id 57 in the config file
empty_df = get_unique_id(parsed_config, 7)


class TestParseConfigurationFile(unittest.TestCase):

    def test_parse_configuration_file_type(self):
        self.assertIsInstance(parsed_config, pd.DataFrame)

    def test_parse_configuration_dimensions(self):
        self.assertEqual(parsed_config.shape, (2, 6))

    def test_parse_configuration_columns(self):
        self.assertEqual(list(parsed_config.columns), columns)


class TestLoadConfig(unittest.TestCase):

    def test_load_config_type(self):
        self.assertIsInstance(parsed_config, pd.DataFrame)

    def test_load_config_dimensions(self):
        self.assertEqual(parsed_config.shape, parsed_config.shape)


class TestGetConfig(unittest.TestCase):

    def test_get_config_not_empty_df(self):
        self.assertEqual(not_empty_df.shape, (1, 6))
        self.assertIsInstance(not_empty_df, pd.DataFrame)
        self.assertEqual(list(not_empty_df), columns)

    def test_get_config_empty_df(self):
        self.assertEqual(empty_df.shape, (0, 6))
        self.assertIsInstance(empty_df, pd.DataFrame)
        self.assertEqual(list(empty_df), columns)
