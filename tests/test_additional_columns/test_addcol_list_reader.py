import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import generate
from gaiaxpy.core.generic_functions import format_additional_columns
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from tests.files.paths import with_missing_bp_csv_file
from tests.utils.utils import parse_dfs_for_test, missing_bp_source_id

sources = [5853498713190525696, missing_bp_source_id, 5762406957886626816]
expected_columns = MANDATORY_INPUT_COLS[generate.__name__] + CORR_INPUT_COLUMNS  # Archive always uses correlations


@pytest.fixture
def setup_data():
    yield {'df': pd.read_csv(with_missing_bp_csv_file)}


@pytest.mark.archive
def test_single_column_test(setup_data):
    additional_columns = format_additional_columns(['solution_id'])
    read_input, _ = InputReader(sources, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(setup_data['df'], read_input, additional_columns,
                                                          expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


@pytest.mark.archive
def test_multiple_columns(setup_data):
    additional_columns = format_additional_columns(['solution_id', 'bp_n_relevant_bases'])
    read_input, _ = InputReader(sources, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(setup_data['df'], read_input, additional_columns,
                                                          expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


@pytest.mark.archive
def test_column_already_in_output(setup_data):
    additional_columns = format_additional_columns(['source_id'])
    read_input, _ = InputReader(sources, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(setup_data['df'], read_input, additional_columns,
                                                          expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


@pytest.mark.archive
def test_multiple_and_already_in_output(setup_data):
    already_in_output = ['bp_standard_deviation', 'rp_coefficients']
    not_in_output = ['solution_id', 'bp_basis_function_id']
    additional_columns = format_additional_columns(already_in_output + not_in_output)
    read_input, _ = InputReader(sources, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(setup_data['df'], read_input, additional_columns,
                                                          expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


@pytest.mark.archive
def test_column_renaming_error():
    additional_columns = format_additional_columns({'source_id': 'bp_n_relevant_bases'})
    with pytest.raises(ValueError):
        read_input, _ = InputReader(sources, generate, additional_columns=additional_columns).read()
