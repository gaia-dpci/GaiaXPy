import unittest

import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import calibrate
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import missing_bp_csv_file, missing_bp_ecsv_file, missing_bp_fits_file, missing_bp_xml_file,\
    missing_bp_xml_plain_file, with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,\
    with_missing_bp_xml_file, with_missing_bp_xml_plain_file
from tests.test_calibrator.calibrator_solutions import sol_with_missing_sampling_array, with_missing_solution_df,\
    missing_solution_df
from tests.utils.utils import npt_array_err_message

_atol = 1e-10
_rtol = 1e-10

cal_with_missing_input_files = [with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,
                                with_missing_bp_xml_file, with_missing_bp_xml_plain_file]
cal_isolated_missing_input_files = [missing_bp_csv_file, missing_bp_ecsv_file, missing_bp_fits_file, missing_bp_xml_file,
                                    missing_bp_xml_plain_file]


class TestCalibratorMissingBPFileInput(unittest.TestCase):

    def test_missing_bp_file(self):
        for file in cal_with_missing_input_files:
            output_df, sampling = calibrate(file, save_file=False)
            npt.assert_array_equal(sampling, sol_with_missing_sampling_array, err_msg=npt_array_err_message(file))
            pdt.assert_frame_equal(output_df, with_missing_solution_df, atol=_atol, rtol=_rtol)

    def test_missing_bp_file_isolated(self):
        for file in cal_isolated_missing_input_files:
            output_df, sampling = calibrate(file, save_file=False)
            npt.assert_array_equal(sampling, sol_with_missing_sampling_array, err_msg=npt_array_err_message(file))
            pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)


class TestCalibratorMissingBPDataFrameInput(unittest.TestCase):

    def test_missing_bp_simple_dataframe(self):
        # Test dataframe containing strings instead of arrays
        df = pd.read_csv(with_missing_bp_csv_file)
        output_df, sampling = calibrate(df, save_file=False)
        pdt.assert_frame_equal(output_df, with_missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_simple_dataframe_isolated(self):
        # Test dataframe containing strings instead of arrays
        df = pd.read_csv(missing_bp_csv_file)
        output_df, sampling = calibrate(df, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_array_dataframe(self):
        # Convert columns in the dataframe to arrays (but not to matrices)
        array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficients',
                         'rp_coefficient_errors', 'rp_coefficient_correlations']
        files = [with_missing_bp_csv_file, missing_bp_csv_file]
        solutions = [with_missing_solution_df, missing_solution_df]
        for file, solution in zip(files, solutions):
            df = pd.read_csv(file, converters=dict([(column, lambda x: str_to_array(x)) for column in array_columns]))
            output_df, sampling = calibrate(df, save_file=False)
            npt.assert_array_equal(sampling, sol_with_missing_sampling_array, err_msg=npt_array_err_message(file))
            pdt.assert_frame_equal(output_df, solution, atol=_atol, rtol=_rtol)

    def test_missing_bp_parsed_dataframe(self):
        # Test completely parsed (arrays + matrices) dataframe
        file = with_missing_bp_csv_file
        df, _ = InputReader(file, calibrate).read()
        output_df, sampling = calibrate(df, save_file=False)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array, err_msg=npt_array_err_message(file))
        pdt.assert_frame_equal(output_df, with_missing_solution_df, atol=_atol, rtol=_rtol)

    def test_missing_bp_parsed_dataframe_isolated(self):
        # Test fully parsed (arrays + matrices) dataframe
        file = missing_bp_csv_file
        df, _ = InputReader(file, calibrate).read()
        output_df, sampling = calibrate(df, save_file=False)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array, err_msg=file)
        pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
