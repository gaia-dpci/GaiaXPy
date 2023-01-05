import unittest
from os import path

import pandas as pd
from numpy import ndarray, dtype

from gaiaxpy.file_parser.parse_generic import DataMismatchError
from gaiaxpy.file_parser.parse_internal_sampled import InternalSampledParser
from tests.files.paths import files_path

# Files to test parse
csv_file = path.join(files_path, 'converter_solution', 'SampledMeanSpectrum.csv')

parser = InternalSampledParser()
parsed_csv_file, _ = parser.parse(csv_file)


class TestInternalSampledParserCSV(unittest.TestCase):

    def test_parse_returns_dataframe(self):
        self.assertIsInstance(parsed_csv_file, pd.DataFrame)

    # 'O' stands for object
    def test_column_types(self):
        self.assertEqual(list(parsed_csv_file.dtypes),
                         [dtype('int64'), dtype('O'), dtype('O'), dtype('O')])

    def test_flux_and_error(self):
        self.assertIsInstance(parsed_csv_file['flux'][0], ndarray)
        self.assertIsInstance(parsed_csv_file['error'][0], ndarray)

    '''
    No sample test files available yet

    def test_parse_fits(self):
        self.assertIsInstance(parser.parse(fits_file), pd.DataFrame)

    def test_parse_xml(self):
        self.assertIsInstance(parser.parse(xml_file), pd.DataFrame)
    '''


class TestIncorrectFormat(unittest.TestCase):

    def test_parse_incorrect_format(self):
        with self.assertRaises(DataMismatchError):
            parser._parse_fits(csv_file)
        with self.assertRaises(DataMismatchError):
            parser._parse_xml(csv_file)
