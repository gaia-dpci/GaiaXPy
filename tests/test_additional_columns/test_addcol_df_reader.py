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


@pytest.fixture
def setup_data():
    yield {'df': pd.read_csv(with_missing_bp_csv_file)}

def test_single_column_test(setup_data):
    df = setup_data['df']
    additional_columns = format_additional_columns(['solution_id'])
    read_input, _ = InputReader(df, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_multiple_columns(setup_data):
    df = setup_data['df']
    additional_columns = format_additional_columns(['solution_id', 'bp_n_relevant_bases'])
    read_input, _ = InputReader(df, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_column_already_in_output(setup_data):
    df = setup_data['df']
    additional_columns = format_additional_columns(['source_id'])
    read_input, _ = InputReader(df, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_multiple_and_already_in_output(setup_data):
    df = setup_data['df']
    already_in_output = ['bp_standard_deviation', 'rp_coefficients']
    not_in_output = ['solution_id', 'bp_basis_function_id']
    additional_columns = format_additional_columns(already_in_output + not_in_output)
    read_input, _ = InputReader(df, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_column_renaming_error(setup_data):
    additional_columns = format_additional_columns({'source_id': 'bp_n_relevant_bases'})
    with pytest.raises(ValueError):
        read_input, _ = InputReader(setup_data['df'], generate, additional_columns=additional_columns).read()


def test_multiple_renaming(setup_data):
    additional_columns = format_additional_columns({'sol_id': 'solution_id', 'bp_id': 'bp_basis_function_id'})
    df = setup_data['df'].rename(columns=reverse_simple_add_col_dict(additional_columns))
    read_input, _ = InputReader(df, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)
