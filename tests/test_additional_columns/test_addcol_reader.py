import numpy as np
import pandas as pd
import numpy.testing as npt
import pandas.testing as pdt
import pytest

from gaiaxpy import generate
from gaiaxpy.core.generic_functions import format_additional_columns
from gaiaxpy.file_parser.cast import _cast
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from tests.files.paths import with_missing_bp_csv_file, with_missing_bp_fits_file
from tests.test_additional_columns.test_addcol_file_reader import type_dict
from tests.utils.utils import parse_dfs_for_test, missing_bp_source_id

expected_columns = MANDATORY_INPUT_COLS[generate.__name__] + CORR_INPUT_COLUMNS

with_missing_bp_df = pd.read_csv(with_missing_bp_csv_file)
with_missing_bp_sources = [5853498713190525696, missing_bp_source_id, 5762406957886626816]
with_missing_bp_query = (f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816',"
                         f"'5853498713190525696', {str(missing_bp_source_id)})")


_atol, _rtol = 1e-6, 1e-6


@pytest.mark.parametrize('input_data', [with_missing_bp_csv_file, with_missing_bp_df, with_missing_bp_sources,
                                        with_missing_bp_query])
def test_single_column_test(input_data):
    additional_columns = format_additional_columns(['solution_id'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(input_data, generate, None, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    expected_df = expected_df.sort_values(by=['source_id'], ignore_index=True)
    filtered_read_input = filtered_read_input.sort_values(by=['source_id'], ignore_index=True)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


@pytest.mark.parametrize('input_data', [with_missing_bp_fits_file, with_missing_bp_df, with_missing_bp_sources,
                                        with_missing_bp_query])
def test_multiple_columns(input_data):
    array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations',
                     'rp_coefficients', 'rp_coefficient_errors', 'rp_coefficient_correlations']
    additional_columns = format_additional_columns(['solution_id', 'bp_n_relevant_bases'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(input_data, generate, False, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    for column in array_columns:
        filtered_read_input[column] = filtered_read_input[column].apply(lambda x: np.nan if (isinstance(
            x, np.ndarray) and len(x) == 0) else x)
    expected_df = _cast(expected_df)
    for key, value in type_dict.items():
        expected_df[key] = expected_df[key].apply(lambda x: x.astype(value) if isinstance(x, np.ndarray) else x)
    expected_df = expected_df.sort_values(by=['source_id'], ignore_index=True)
    filtered_read_input = filtered_read_input.sort_values(by=['source_id'], ignore_index=True)
    # Check NumPy arrays separately due to issue
    for column in array_columns:
        for index in range(len(expected_df)):
            npt.assert_array_almost_equal(expected_df[column].iloc[index], filtered_read_input[column].iloc[index],
                                          decimal=5)
    untested_columns = list(set(expected_df.columns) - set(array_columns))
    pdt.assert_frame_equal(expected_df[untested_columns], filtered_read_input[untested_columns], check_like=True,
                           check_dtype=False, check_exact=False)
