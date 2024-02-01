import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import convert
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from tests.files.paths import mean_spectrum_csv_file

columns_to_read = MANDATORY_INPUT_COLS['convert'] + CORR_INPUT_COLUMNS
dataframe_str = pd.read_csv(mean_spectrum_csv_file, float_precision='round_trip', usecols=columns_to_read)
parser = InternalContinuousParser(columns_to_read)
dataframe_np, _ = parser.parse_file(mean_spectrum_csv_file)
# Temporarily opt for removing cov matrices before comparing
dataframe_np = dataframe_np.drop(columns=['bp_covariance_matrix', 'rp_covariance_matrix'])

_rtol, _atol = 1e-24, 1e-24


def test_dfs():
    parsed_df_str, _ = InputReader(dataframe_str, convert).read()
    parsed_df_np, _ = InputReader(dataframe_np, convert).read()
    pdt.assert_frame_equal(parsed_df_str, parsed_df_np, rtol=_rtol, atol=_atol)


def test_empty_list():
    with pytest.raises(ValueError):
        input_reader, _ = InputReader([], convert).read()
