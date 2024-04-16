import json

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import convert
from gaiaxpy.core.generic_functions import correlation_to_covariance
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from tests.files.paths import (with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,
                               with_missing_bp_xml_file, with_missing_bp_xml_plain_file, input_reader_solution_path)
from tests.utils.utils import parse_matrices

CON_COLS = MANDATORY_INPUT_COLS['convert'] + CORR_INPUT_COLUMNS

ir_solution_array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations',
                             'rp_coefficients', 'rp_coefficient_errors', 'rp_coefficient_correlations']
ir_masked_constant_columns = ['bp_n_parameters']
ir_array_converters = dict([(column, lambda x: parse_matrices(x)) for column in ir_solution_array_columns])

input_reader_solution_df = pd.read_csv(input_reader_solution_path, converters=ir_array_converters, usecols=CON_COLS)
for column in ir_masked_constant_columns:
    input_reader_solution_df[column] = input_reader_solution_df[column].astype('Int64')
# Create covariance matrices
for band in BANDS:
    input_reader_solution_df[f'{band}_covariance_matrix'] = input_reader_solution_df.apply(
        lambda x: correlation_to_covariance(x[f'{band}_coefficient_correlations'], x[f'{band}_coefficient_errors'],
                                            x[f'{band}_standard_deviation']), axis=1)

_rtol, _atol = 1e-6, 1e-6


def _convert_to_nan(arr):
    return np.nan if isinstance(arr, np.ndarray) and arr.size == 0 else arr


def __parse_matrices_custom(string):
    return np.nan if len(string) == 0 else np.array(json.loads(string))


def check_special_columns(columns, data, solution):
    for column in columns:
        for i in range(len(data)):
            d = data[column].iloc[i]
            s = solution[column].iloc[i]
            if not isinstance(d, np.ndarray):
                pass
            else:
                npt.assert_array_almost_equal(d, s, decimal=5)


# Missing BP source not available in AVRO format

def test_file_missing_bp():
    input_files = [with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_xml_plain_file]
    for file in input_files:
        parsed_data_file, _ = InputReader(file, convert, False).read()
        for column in ir_solution_array_columns:
            parsed_data_file[column] = parsed_data_file[column].apply(lambda x: _convert_to_nan(x))
        pdt.assert_frame_equal(parsed_data_file, input_reader_solution_df, rtol=_rtol, atol=_atol, check_dtype=False,
                               check_like=True)


def test_fits_file_missing_bp():
    parsed_data_file, _ = InputReader(with_missing_bp_fits_file, convert, False).read()
    columns_to_drop = ['bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficient_errors']
    check_special_columns(columns_to_drop, parsed_data_file, input_reader_solution_df)
    for column in ir_solution_array_columns:
        parsed_data_file[column] = parsed_data_file[column].apply(lambda x: _convert_to_nan(x))
    parsed_data_file = parsed_data_file.drop(columns=columns_to_drop)
    solution_df = input_reader_solution_df.drop(columns=columns_to_drop)
    pdt.assert_frame_equal(parsed_data_file, solution_df, rtol=_rtol, atol=_atol, check_dtype=False, check_like=True)


def test_xml_file_missing_bp():
    parsed_data_file, _ = InputReader(with_missing_bp_xml_file, convert, False).read()
    columns_to_drop = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations',
                       'rp_coefficient_errors']
    check_special_columns(columns_to_drop, parsed_data_file, input_reader_solution_df)
    parsed_data_file = parsed_data_file.drop(columns=columns_to_drop)
    solution_df = input_reader_solution_df.drop(columns=columns_to_drop)
    pdt.assert_frame_equal(parsed_data_file, solution_df, rtol=_rtol, atol=_atol, check_dtype=False, check_like=True)
