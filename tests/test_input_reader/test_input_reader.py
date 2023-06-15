import unittest
from os import path

import pandas as pd
import pandas.testing as pdt

from gaiaxpy import convert
from gaiaxpy.core.generic_variables import INTERNAL_CONT_COLS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import files_path

file_path = path.join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW.csv')
dataframe_str = pd.read_csv(file_path, float_precision='high', usecols=INTERNAL_CONT_COLS)
parser = InternalContinuousParser()
dataframe_np, _ = parser._parse(file_path)
# Temporarily opt for removing cov matrices before comparing
dataframe_np = dataframe_np.drop(columns=['bp_covariance_matrix', 'rp_covariance_matrix'])

_rtol, _atol = 1e-24, 1e-24


class TestGetMethods(unittest.TestCase):

    def test_dfs(self):
        parsed_df_str, _ = InputReader(dataframe_str, convert).read()
        parsed_df_np, _ = InputReader(dataframe_np, convert).read()
        pdt.assert_frame_equal(parsed_df_str, parsed_df_np, rtol=_rtol, atol=_atol)

    def test_empty_list(self):
        with self.assertRaises(ValueError):
            input_reader, _ = InputReader([], convert).read()
