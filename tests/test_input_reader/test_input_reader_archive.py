import unittest
from os import path

import pandas as pd
import pandas.testing as pdt

from gaiaxpy import calibrate
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import files_path

file_path = path.join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW.csv')
dataframe_str = pd.read_csv(file_path, float_precision='high')
parser = InternalContinuousParser()
dataframe_np, _ = parser._parse(file_path)

_rtol, _atol = 1e-24, 1e-24


class TestGetMethods(unittest.TestCase):

    def test_path_vs_query(self):
        # Calibrator requires use of internal calibrate function
        query_input = "SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816'," \
                      "'5853498713190525696')"
        parsed_data_file, _ = InputReader(file_path, calibrate).read()
        parsed_data_query, _ = InputReader(query_input, calibrate).read()
        # The Archive will return all columns, not only the ones required by the tools
        parsed_data_query = parsed_data_query[parsed_data_file.columns]
        # Windows version returns different dtypes
        parsed_data_query = parsed_data_query.astype({'source_id': 'int64', 'solution_id': 'int64'})
        pdt.assert_frame_equal(parsed_data_file.sort_values('source_id', ignore_index=True), parsed_data_query,
                               rtol=_rtol, atol=_atol, check_dtype=False)
