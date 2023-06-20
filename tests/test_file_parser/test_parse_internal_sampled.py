import unittest
from os import path

import pandas as pd
from numpy import ndarray, dtype

from gaiaxpy.file_parser.parse_internal_sampled import InternalSampledParser
from tests.files.paths import converter_sol_path

# Files to test parse
csv_file = path.join(converter_sol_path, 'SampledMeanSpectrum.csv')

parser = InternalSampledParser()
parsed_csv_file, _ = parser._parse(csv_file)


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
