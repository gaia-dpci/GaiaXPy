import numpy as np
import pandas as pd
import numpy.testing as npt
import pandas.testing as pdt
import pytest

from gaiaxpy import generate
from gaiaxpy.core.generic_functions import format_additional_columns, reverse_simple_add_col_dict
from gaiaxpy.file_parser.cast import _cast
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from tests.files.paths import with_missing_bp_csv_file, with_missing_bp_fits_file, with_missing_bp_xml_file, \
    with_missing_bp_xml_plain_file, with_missing_bp_ecsv_file
from tests.utils.utils import parse_dfs_for_test, missing_bp_source_id

expected_columns = MANDATORY_INPUT_COLS[generate.__name__] + CORR_INPUT_COLUMNS

with_missing_bp_df = pd.read_csv(with_missing_bp_csv_file)
with_missing_bp_sources = [5853498713190525696, missing_bp_source_id, 5762406957886626816]
with_missing_bp_query = (f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816',"
                         f"'5853498713190525696', {str(missing_bp_source_id)})")

array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations',
                 'rp_coefficients', 'rp_coefficient_errors', 'rp_coefficient_correlations']
type_dict = {'bp_coefficients': np.float64, 'bp_coefficient_errors': np.float32, 'bp_coefficient_correlations':
    np.float32, 'rp_coefficient_errors': np.float32}

@pytest.mark.parametrize('input_data', [with_missing_bp_csv_file, with_missing_bp_df,
                                        pytest.param(with_missing_bp_sources, marks=pytest.mark.archive),
                                        pytest.param(with_missing_bp_query, marks=pytest.mark.archive)])
def test_single_column_test(input_data):
    additional_columns = format_additional_columns(['solution_id'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(input_data, generate, None, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    expected_df = expected_df.sort_values(by=['source_id'], ignore_index=True)
    filtered_read_input = filtered_read_input.sort_values(by=['source_id'], ignore_index=True)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def run_numpy_comparison(expected_df, read_input, _array_columns):
    for column in _array_columns:
        for index in range(len(expected_df)):
            npt.assert_array_almost_equal(expected_df[column].iloc[index], read_input[column].iloc[index], decimal=5)

@pytest.mark.parametrize('input_data', [with_missing_bp_fits_file, with_missing_bp_df,
                                        pytest.param(with_missing_bp_sources, marks=pytest.mark.archive),
                                        pytest.param(with_missing_bp_query, marks=pytest.mark.archive)])
def test_multiple_columns(input_data):
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
    run_numpy_comparison(expected_df, filtered_read_input, array_columns)
    untested_columns = list(set(expected_df.columns) - set(array_columns))
    pdt.assert_frame_equal(expected_df[untested_columns], filtered_read_input[untested_columns], check_like=True,
                           check_dtype=False, check_exact=False)


@pytest.mark.parametrize('input_data', [with_missing_bp_xml_file, with_missing_bp_df,
                                        pytest.param(with_missing_bp_sources, marks=pytest.mark.archive),
                                        pytest.param(with_missing_bp_query, marks=pytest.mark.archive)])
def test_column_already_in_output(input_data):
    additional_columns = format_additional_columns(['source_id'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(input_data, generate, False, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    expected_df = expected_df.sort_values(by=['source_id'], ignore_index=True)
    filtered_read_input = filtered_read_input.sort_values(by=['source_id'], ignore_index=True)
    # Check NumPy arrays separately due to issue with pandas testing
    run_numpy_comparison(expected_df, filtered_read_input, array_columns)
    untested_columns = list(set(expected_df.columns) - set(array_columns))
    pdt.assert_frame_equal(expected_df[untested_columns], filtered_read_input[untested_columns], check_like=True,
                           check_dtype=False)


@pytest.mark.parametrize('input_data', [with_missing_bp_xml_plain_file, with_missing_bp_df,
                                        pytest.param(with_missing_bp_sources, marks=pytest.mark.archive),
                                        pytest.param(with_missing_bp_query, marks=pytest.mark.archive)])
def test_multiple_and_already_in_output(input_data):
    additional_columns = format_additional_columns(['bp_standard_deviation', 'rp_coefficients', 'solution_id',
                                                    'bp_basis_function_id'])
    df = pd.read_csv(with_missing_bp_csv_file)
    read_input, _ = InputReader(input_data, generate, False, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    expected_df = _cast(expected_df)
    expected_df = expected_df.sort_values(by=['source_id'], ignore_index=True)
    filtered_read_input = filtered_read_input.sort_values(by=['source_id'], ignore_index=True)
    for key, value in type_dict.items():
        expected_df[key] = expected_df[key].apply(lambda x: x.astype(value) if isinstance(x, np.ndarray) else x)
    # Check NumPy arrays separately due to issue with pandas testing
    run_numpy_comparison(expected_df, filtered_read_input, array_columns)
    untested_columns = list(set(expected_df.columns) - set(array_columns))
    pdt.assert_frame_equal(expected_df[untested_columns], filtered_read_input[untested_columns], check_like=True,
                           check_dtype=False)


@pytest.mark.parametrize('input_data', [with_missing_bp_ecsv_file, with_missing_bp_df,
                                        pytest.param(with_missing_bp_sources, marks=pytest.mark.archive),
                                        pytest.param(with_missing_bp_query, marks=pytest.mark.archive)])
def test_column_renaming_error(input_data):
    additional_columns = format_additional_columns({'source_id': 'bp_n_relevant_bases'})
    with pytest.raises(ValueError):
        read_input, _ = InputReader(input_data, generate, False, additional_columns=additional_columns).read()


@pytest.mark.parametrize('input_data', [with_missing_bp_csv_file, with_missing_bp_df,
                                        pytest.param(with_missing_bp_sources, marks=pytest.mark.archive),
                                        pytest.param(with_missing_bp_query, marks=pytest.mark.archive)])
def test_multiple_renaming(input_data):
    additional_columns = format_additional_columns({'sol_id': 'solution_id', 'bp_id': 'bp_basis_function_id'})
    df = pd.read_csv(with_missing_bp_csv_file).rename(columns=reverse_simple_add_col_dict(additional_columns))
    read_input, _ = InputReader(input_data, generate, False, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(df, read_input, additional_columns, expected_columns)
    expected_df = expected_df.sort_values(by=['source_id'], ignore_index=True)
    filtered_read_input = filtered_read_input.sort_values(by=['source_id'], ignore_index=True)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)
