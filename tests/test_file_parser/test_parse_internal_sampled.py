import unittest

import pandas as pd
from numpy import ndarray, dtype

from gaiaxpy.file_parser.parse_internal_sampled import InternalSampledParser
from tests.files.paths import con_ref_sampled_csv_path

parser = InternalSampledParser()
parsed_csv_file, _ = parser._parse(con_ref_sampled_csv_path)


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
