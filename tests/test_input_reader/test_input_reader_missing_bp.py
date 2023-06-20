import unittest
from os.path import join

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import convert
from gaiaxpy.core.generic_variables import INTERNAL_CONT_COLS
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import files_path, with_missing_bp_csv_file, with_missing_bp_ecsv_file, \
    with_missing_bp_fits_file, with_missing_bp_xml_file, with_missing_bp_xml_plain_file
from tests.utils.utils import parse_matrices

solution_file = join(files_path, 'input_reader_solution.csv')
solution_array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficients',
                          'rp_coefficient_errors', 'rp_coefficient_correlations']
masked_constant_columns = ['bp_basis_function_id', 'bp_n_parameters', 'bp_n_relevant_bases']

array_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])

solution_df = pd.read_csv(solution_file, converters=array_converters, usecols=INTERNAL_CONT_COLS)
for column in masked_constant_columns:
    solution_df[column] = solution_df[column].astype('Int64')

_rtol, _atol = 1e-7, 1e-7


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
class TestInputReaderMissingBPFile(unittest.TestCase):

    def test_csv_file_missing_bp(self):
        parsed_data_file, _ = InputReader(with_missing_bp_csv_file, convert).read()
        # Temporarily opt for removing cov matrices before comparing
        parsed_data_file = parsed_data_file.drop(columns=['bp_covariance_matrix', 'rp_covariance_matrix'])
        pdt.assert_frame_equal(parsed_data_file, solution_df, rtol=_rtol, atol=_atol)

    def test_ecsv_file_missing_bp(self):
        parsed_data_file, _ = InputReader(with_missing_bp_ecsv_file, convert).read()
        # Temporarily opt for removing cov matrices before comparing
        parsed_data_file = parsed_data_file.drop(columns=['bp_covariance_matrix', 'rp_covariance_matrix'])
        pdt.assert_frame_equal(parsed_data_file, solution_df, rtol=_rtol, atol=_atol)

    def test_fits_file_missing_bp(self):
        solution_df = pd.read_csv(solution_file, converters=array_converters, usecols=INTERNAL_CONT_COLS)
        parsed_data_file, _ = InputReader(with_missing_bp_fits_file, convert).read()
        columns_to_drop = ['bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficient_errors']
        check_special_columns(columns_to_drop, parsed_data_file, solution_df)
        parsed_data_file = parsed_data_file.drop(columns=columns_to_drop)
        solution_df = solution_df.drop(columns=columns_to_drop)
        # Temporarily opt for removing cov matrices before comparing
        parsed_data_file = parsed_data_file.drop(columns=['bp_covariance_matrix', 'rp_covariance_matrix'])
        pdt.assert_frame_equal(parsed_data_file, solution_df, rtol=_rtol, atol=_atol, check_dtype=False)

    def test_xml_file_missing_bp(self):
        solution_df = pd.read_csv(solution_file, converters=array_converters, usecols=INTERNAL_CONT_COLS)
        parsed_data_file, _ = InputReader(with_missing_bp_xml_file, convert).read()
        columns_to_drop = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations',
                           'rp_coefficient_errors']
        check_special_columns(columns_to_drop, parsed_data_file, solution_df)
        parsed_data_file = parsed_data_file.drop(columns=columns_to_drop)
        # Temporarily opt for removing cov matrices before comparing
        parsed_data_file = parsed_data_file.drop(columns=['bp_covariance_matrix', 'rp_covariance_matrix'])
        solution_df = solution_df.drop(columns=columns_to_drop)
        pdt.assert_frame_equal(parsed_data_file, solution_df, rtol=_rtol, atol=_atol, check_dtype=False)

    def test_xml_plain_file_missing_bp(self):
        parsed_data_file, _ = InputReader(with_missing_bp_xml_plain_file, convert).read()
        # Temporarily opt for removing cov matrices before comparing
        parsed_data_file = parsed_data_file.drop(columns=['bp_covariance_matrix', 'rp_covariance_matrix'])
        pdt.assert_frame_equal(parsed_data_file, solution_df, rtol=_rtol, atol=_atol, check_dtype=False)
