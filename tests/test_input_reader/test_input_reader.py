import unittest
from os import path

import pandas as pd
import pandas.testing as pdt

from gaiaxpy import calibrate, convert
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import files_path

file_path = path.join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW.csv')
dataframe_str = pd.read_csv(file_path, float_precision='round_trip')
parser = InternalContinuousParser()
dataframe_np, _ = parser.parse(file_path)

_rtol, _atol = 1e-24, 1e-24


class TestGetMethods(unittest.TestCase):

    # Commented because it requires credentials to run
    def test_path_vs_query(self):
        # Calibrator requires use of internal calibrate function
        query_input = "SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816'," \
                      "'5853498713190525696')"
        parsed_data_file, _ = InputReader(file_path, calibrate)._read()
        parsed_data_query, _ = InputReader(query_input, calibrate)._read()
        # Windows version returns different dtypes
        parsed_data_query = parsed_data_query.astype({'source_id': 'int64', 'solution_id': 'int64'})
        pdt.assert_frame_equal(parsed_data_file.sort_values('source_id', ignore_index=True), parsed_data_query,
                               rtol=_rtol, atol=_atol, check_dtype=False)

    def test_dfs(self):
        parsed_df_str, _ = InputReader(dataframe_str, convert)._read()
        parsed_df_np, _ = InputReader(dataframe_np, convert)._read()
        pdt.assert_frame_equal(parsed_df_str, parsed_df_np, rtol=_rtol, atol=_atol)

    def test_empty_list(self):
        with self.assertRaises(ValueError):
            input_reader, _ = InputReader([], convert)._read()
