import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import generate
from gaiaxpy.core.generic_functions import format_additional_columns
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from tests.files.paths import with_missing_bp_csv_file
from tests.utils.utils import parse_dfs_for_test, missing_bp_source_id

query = ("SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816', '5853498713190525696', "
         f"{str(missing_bp_source_id)})")
expected_columns = MANDATORY_INPUT_COLS[generate.__name__] + CORR_INPUT_COLUMNS  # Archive always uses correlations


def test_single_column_test():
    additional_columns = format_additional_columns(['solution_id'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(query, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    expected_df = expected_df.sort_values(by=['source_id'], ignore_index=True)
    filtered_read_input = filtered_read_input.sort_values(by=['source_id'], ignore_index=True)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_multiple_columns():
    additional_columns = format_additional_columns(['solution_id', 'bp_n_relevant_bases'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(query, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    expected_df = expected_df.sort_values(by=['source_id'], ignore_index=True)
    filtered_read_input = filtered_read_input.sort_values(by=['source_id'], ignore_index=True)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_column_already_in_output():
    additional_columns = format_additional_columns(['source_id'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(query, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    expected_df = expected_df.sort_values(by=['source_id'], ignore_index=True)
    filtered_read_input = filtered_read_input.sort_values(by=['source_id'], ignore_index=True)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_multiple_and_already_in_output():
    # First two are in already in the output, the other columns are not
    additional_columns = format_additional_columns(['bp_standard_deviation', 'rp_coefficients', 'solution_id',
                                                    'bp_basis_function_id'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(query, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    expected_df = expected_df.sort_values(by=['source_id'], ignore_index=True)
    filtered_read_input = filtered_read_input.sort_values(by=['source_id'], ignore_index=True)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_column_renaming_error():
    additional_columns = format_additional_columns({'source_id': 'bp_n_relevant_bases'})
    with pytest.raises(ValueError):
        read_input, _ = InputReader(query, generate, additional_columns=additional_columns).read()
