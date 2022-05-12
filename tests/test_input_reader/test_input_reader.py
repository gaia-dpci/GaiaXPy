import unittest
import pandas as pd
import pandas.testing as pdt
from gaiaxpy import convert
from gaiaxpy.input_reader import InputReader
from gaiaxpy.file_parser import InternalContinuousParser
from tests.files import files_path
from os import path

file_path = path.join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_dr3int6.csv')
dataframe_str = pd.read_csv(file_path, float_precision='round_trip')
parser = InternalContinuousParser()
dataframe_np, _ = parser.parse(file_path)
list_input_int = [4, 6]
list_input_str = ['4', '6']
query_input = "SELECT * FROM user_dr3int6.gaia_source WHERE source_id IN ('4', '6')"


class TestGetMethods(unittest.TestCase):

    '''
    # Commented because it requires credentials to run
    def test_path_vs_query(self):
        # Calibrator requires use of internal calibrate function
        parsed_data_file_path, _ = InputReader(file_path, calibrate)._read()
        parsed_data_query_input, _ = InputReader(query_input, calibrate)._read()
        pdt.assert_frame_equal(parsed_data_file_path, parsed_data_query_input)
    '''

    def test_dfs(self):
        parsed_df_str, _ = InputReader(dataframe_str, convert)._read()
        parsed_df_np, _ = InputReader(dataframe_np, convert)._read()
        pdt.assert_frame_equal(parsed_df_str, parsed_df_np)

    def test_empty_list(self):
        with self.assertRaises(ValueError):
            input_reader, _ = InputReader([], convert)._read()
