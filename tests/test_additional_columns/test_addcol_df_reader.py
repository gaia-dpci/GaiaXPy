import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import generate
from gaiaxpy.core.generic_functions import format_additional_columns, reverse_simple_add_col_dict
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from tests.files.paths import with_missing_bp_csv_file
from tests.utils.utils import parse_dfs_for_test

expected_columns = MANDATORY_INPUT_COLS[generate.__name__] + CORR_INPUT_COLUMNS


def test_single_column_test():
    additional_columns = format_additional_columns(['solution_id'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(df, generate, None, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_multiple_columns():
    additional_columns = format_additional_columns(['solution_id', 'bp_n_relevant_bases'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(df, generate, None, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_column_already_in_output():
    additional_columns = format_additional_columns(['source_id'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(df, generate, None, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_multiple_and_already_in_output():
    # First two are in already in the output, the other columns are not
    additional_columns = format_additional_columns(['bp_standard_deviation', 'rp_coefficients', 'solution_id',
                                                    'bp_basis_function_id'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(df, generate, None, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_column_renaming_error():
    additional_columns = format_additional_columns({'source_id': 'bp_n_relevant_bases'})
    df = pd.read_csv(with_missing_bp_csv_file)
    with pytest.raises(ValueError):
        read_input, _ = InputReader(df, generate, None, additional_columns=additional_columns).read()


def test_multiple_renaming():
    additional_columns = format_additional_columns({'sol_id': 'solution_id', 'bp_id': 'bp_basis_function_id'})
    df = pd.read_csv(with_missing_bp_csv_file).rename(columns=reverse_simple_add_col_dict(additional_columns))
    read_input, _ = InputReader(df, generate, None, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)
