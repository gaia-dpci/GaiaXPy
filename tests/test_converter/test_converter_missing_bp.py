import unittest

import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import convert
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import missing_bp_csv_file, missing_bp_ecsv_file, missing_bp_fits_file, missing_bp_xml_file, \
    missing_bp_xml_plain_file, with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file, \
    with_missing_bp_xml_file, with_missing_bp_xml_plain_file
from tests.test_converter.converter_paths import with_missing_solution_df, with_missing_solution_sampling, \
    missing_solution_df

_rtol, _atol = 1e-7, 1e-7

con_with_missing_input_files = [with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,
                                with_missing_bp_xml_file, with_missing_bp_xml_plain_file]
con_isolated_missing_input_files = [missing_bp_csv_file, missing_bp_ecsv_file, missing_bp_fits_file, missing_bp_xml_file,
                                    missing_bp_xml_plain_file]

class TestConverterMissingBPFileInput(unittest.TestCase):

    def test_with_missing_bp_file(self):
        for file in con_with_missing_input_files:
            output_df, sampling = convert(file, save_file=False)
            npt.assert_array_equal(sampling, with_missing_solution_sampling)
            pdt.assert_frame_equal(output_df, with_missing_solution_df, rtol=_rtol, atol=_atol)

    def test_missing_bp_file_isolated(self):
        for file in con_isolated_missing_input_files:
            output_df, sampling = convert(file, save_file=False)
            pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
            npt.assert_array_equal(sampling, with_missing_solution_sampling)


class TestConverterMissingBPDataFrameInput(unittest.TestCase):

    def test_missing_bp_simple_dataframe(self):
        # Test dataframe containing strings instead of arrays
        df = pd.read_csv(with_missing_bp_csv_file)
        output_df, sampling = convert(df, save_file=False)
        pdt.assert_frame_equal(output_df, with_missing_solution_df, rtol=_rtol, atol=_atol)
        npt.assert_array_equal(sampling, with_missing_solution_sampling)

    def test_missing_bp_simple_dataframe_isolated(self):
        # Test dataframe containing strings instead of arrays
        df = pd.read_csv(missing_bp_csv_file)
        output_df, sampling = convert(df, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, with_missing_solution_sampling)

    def test_missing_bp_array_dataframe(self):
        # Convert columns in the dataframe to arrays (but not to matrices)
        array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficients',
                         'rp_coefficient_errors', 'rp_coefficient_correlations']
        _converters = dict([(column, lambda x: str_to_array(x)) for column in array_columns])
        inputs = [with_missing_bp_csv_file, missing_bp_csv_file]
        solutions = [with_missing_solution_df, missing_solution_df]
        for _input, solution in zip(inputs, solutions):
            df = pd.read_csv(_input, converters=_converters)
            output_df, sampling = convert(df, save_file=False)
            pdt.assert_frame_equal(output_df, solution, rtol=_rtol, atol=_atol)
            npt.assert_array_equal(sampling, with_missing_solution_sampling)

    def test_missing_bp_parsed_dataframe(self):
        # Test completely parsed (arrays + matrices) dataframe
        inputs = [with_missing_bp_csv_file, missing_bp_csv_file]
        solutions = [with_missing_solution_df, missing_solution_df]
        for _input, solution in zip(inputs, solutions):
            df, _ = InputReader(_input, convert).read()
            output_df, sampling = convert(df, save_file=False)
            pdt.assert_frame_equal(output_df, solution, rtol=_rtol, atol=_atol)
            npt.assert_array_equal(sampling, with_missing_solution_sampling)
