import unittest
import numpy as np
import pandas as pd
import numpy.testing as npt
import pandas.testing as pdt
from os.path import join
from tests.files import files_path
from tests.utils.utils import parse_matrices
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy import convert


solution_file = join(files_path, 'input_reader_solution.csv')
solution_array_columns = ['bp_coefficients', 'bp_coefficient_errors', \
                          'bp_coefficient_correlations', 'rp_coefficients', \
                          'rp_coefficient_errors', 'rp_coefficient_correlations']
solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
solution_df = pd.read_csv(solution_file, converters=solution_converters)

xp_continuous_path = join(files_path, 'xp_continuous')


def check_special_columns(columns, data, solution):
    for column in columns:
        for i in range(len(data)):
            d = data[column].iloc[i]; s = solution[column].iloc[i]
            if (not isinstance(d, np.ndarray) and not isinstance(d, np.ndarray)):
                pass
            else:
                npt.assert_array_almost_equal(d, s, decimal=5)

# Missing BP source not available in AVRO format
class TestInputReaderMissingBPFile(unittest.TestCase):

    def test_csv_file_missing_bp(self):
        file = join(xp_continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
        parsed_data_file, _ = InputReader(file, convert)._read()
        pdt.assert_frame_equal(parsed_data_file, solution_df)

    def test_ecsv_file_missing_bp(self):
        file = join(xp_continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.ecsv')
        parsed_data_file, _ = InputReader(file, convert)._read()
        pdt.assert_frame_equal(parsed_data_file, solution_df)

    def test_fits_file_missing_bp(self):
        solution_df = pd.read_csv(solution_file, converters=solution_converters)
        file = join(xp_continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.fits')
        parsed_data_file, _ = InputReader(file, convert)._read()
        columns_to_drop = ['bp_coefficient_errors', 'bp_coefficient_correlations', \
                           'rp_coefficient_errors']
        check_special_columns(columns_to_drop, parsed_data_file, solution_df)
        parsed_data_file = parsed_data_file.drop(columns=columns_to_drop)
        solution_df = solution_df.drop(columns=columns_to_drop)
        pdt.assert_frame_equal(parsed_data_file, solution_df, check_dtype=False)

    def test_xml_file_missing_bp(self):
        solution_df = pd.read_csv(solution_file, converters=solution_converters)
        file = join(xp_continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.xml')
        parsed_data_file, _ = InputReader(file, convert)._read()
        columns_to_drop = ['bp_coefficients', 'bp_coefficient_errors', \
                           'bp_coefficient_correlations', 'rp_coefficient_errors']
        check_special_columns(columns_to_drop, parsed_data_file, solution_df)
        parsed_data_file = parsed_data_file.drop(columns=columns_to_drop)
        solution_df = solution_df.drop(columns=columns_to_drop)
        pdt.assert_frame_equal(parsed_data_file, solution_df, check_dtype=False)

    def test_xml_plain_file_missing_bp(self):
        file = join(xp_continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP_plain.xml')
        parsed_data_file, _ = InputReader(file, convert)._read()
        pdt.assert_frame_equal(parsed_data_file, solution_df, check_dtype=False)
