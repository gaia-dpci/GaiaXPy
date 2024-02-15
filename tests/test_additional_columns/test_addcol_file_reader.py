import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import generate
from gaiaxpy.core.generic_functions import format_additional_columns
from gaiaxpy.file_parser.cast import _cast
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from tests.files.paths import (with_missing_bp_csv_file, with_missing_bp_fits_file, with_missing_bp_xml_file,
                               with_missing_bp_ecsv_file)
from tests.utils.utils import parse_dfs_for_test

expected_columns = MANDATORY_INPUT_COLS[generate.__name__] + CORR_INPUT_COLUMNS

type_dict = {'bp_coefficients': np.float64, 'bp_coefficient_errors': np.float32,
             'bp_coefficient_correlations': np.float32, 'rp_coefficient_errors': np.float32}


@pytest.fixture
def setup_data():
    yield {'df': pd.read_csv(with_missing_bp_csv_file)}


def test_single_column(setup_data):
    additional_columns = format_additional_columns(['solution_id'])
    read_input, _ = InputReader(with_missing_bp_csv_file, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(setup_data['df'], read_input, additional_columns,
                                                          expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_multiple_columns(setup_data):
    additional_columns = format_additional_columns(['solution_id', 'bp_n_relevant_bases'])
    read_input, _ = InputReader(with_missing_bp_fits_file, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(setup_data['df'], read_input, additional_columns,
                                                          expected_columns)
    for column in ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations']:
        filtered_read_input[column] = filtered_read_input[column].apply(lambda x: np.nan if (isinstance(
            x, np.ndarray) and len(x) == 0) else x)
    expected_df = _cast(expected_df)
    for key, value in type_dict.items():
        expected_df[key] = expected_df[key].apply(lambda x: x.astype(value) if isinstance(x, np.ndarray) else x)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False, check_exact=False)


def test_column_already_in_output(setup_data):
    additional_columns = format_additional_columns(['source_id'])
    read_input, _ = InputReader(with_missing_bp_ecsv_file, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(setup_data['df'], read_input, additional_columns,
                                                          expected_columns)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_multiple_and_already_in_output(setup_data):
    already_in_output = ['bp_standard_deviation', 'rp_coefficients']
    not_in_output = ['solution_id', 'bp_basis_function_id']
    additional_columns = format_additional_columns(already_in_output + not_in_output)
    read_input, _ = InputReader(with_missing_bp_xml_file, generate, additional_columns=additional_columns).read()
    expected_df, filtered_read_input = parse_dfs_for_test(setup_data['df'], read_input, additional_columns,
                                                          expected_columns)
    expected_df = _cast(expected_df)
    for key, value in type_dict.items():
        expected_df[key] = expected_df[key].apply(lambda x: x.astype(value) if isinstance(x, np.ndarray) else x)
    pdt.assert_frame_equal(expected_df, filtered_read_input, check_like=True, check_dtype=False)


def test_column_renaming_error():
    additional_columns = format_additional_columns({'source_id': 'bp_n_relevant_bases'})
    with pytest.raises(ValueError):
        read_input, _ = InputReader(with_missing_bp_csv_file, generate, additional_columns=additional_columns).read()
