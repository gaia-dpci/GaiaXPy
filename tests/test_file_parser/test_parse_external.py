import unittest
from os import path

import pandas as pd
from numpy import ndarray, dtype

from gaiaxpy.file_parser.parse_external import ExternalParser
from gaiaxpy.file_parser.parse_generic import InvalidExtensionError
from tests.files.paths import mini_csv_file, no_ext_file

parser = ExternalParser()
parsed_csv_file = parser._parse_csv(mini_csv_file)


class TestExternalParserCSV(unittest.TestCase):

    def test_parse_no_extension(self):
        self.assertRaises(InvalidExtensionError, parser._parse, no_ext_file)

    def test_parse_returns_dataframe(self):
        self.assertIsInstance(parsed_csv_file, pd.DataFrame)

    # 'O' stands for object
    def test_column_types(self):
        self.assertEqual(list(parsed_csv_file.dtypes),
                         [dtype('int64'), dtype('O'), dtype('O'), dtype('O')])

    def test_flux_types(self):
        self.assertIsInstance(parsed_csv_file['flux'][0], ndarray)
        self.assertIsInstance(parsed_csv_file['flux_error'][0], ndarray)
