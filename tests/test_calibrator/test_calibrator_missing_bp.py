import unittest

import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import calibrate
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import missing_bp_csv_file, missing_bp_ecsv_file, missing_bp_fits_file, missing_bp_xml_file, \
    missing_bp_xml_plain_file, with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file, \
    with_missing_bp_xml_file, with_missing_bp_xml_plain_file
from tests.test_calibrator.calibrator_paths import sol_with_missing_sampling_array, with_missing_solution_df, \
    missing_solution_df

_atol = 1e-10
_rtol = 1e-10


class TestCalibratorMissingBPFileInput(unittest.TestCase):

    def test_missing_bp_csv_file(self):
        output_df, sampling = calibrate(with_missing_bp_csv_file, save_file=False)
        pdt.assert_frame_equal(output_df, with_missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_ecsv_file(self):
        output_df, sampling = calibrate(with_missing_bp_ecsv_file, save_file=False)
        pdt.assert_frame_equal(output_df, with_missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_fits_file(self):
        output_df, sampling = calibrate(with_missing_bp_fits_file, save_file=False)
        pdt.assert_frame_equal(output_df, with_missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_xml_file(self):
        output_df, sampling = calibrate(with_missing_bp_xml_file, save_file=False)
        pdt.assert_frame_equal(output_df, with_missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_xml_plain_file(self):
        output_df, sampling = calibrate(with_missing_bp_xml_plain_file, save_file=False)
        pdt.assert_frame_equal(output_df, with_missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_csv_file_isolated(self):
        output_df, sampling = calibrate(missing_bp_csv_file, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_ecsv_file_isolated(self):
        output_df, sampling = calibrate(missing_bp_ecsv_file, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_fits_file_isolated(self):
        output_df, sampling = calibrate(missing_bp_fits_file, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_xml_file_isolated(self):
        output_df, sampling = calibrate(missing_bp_xml_file, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_xml_plain_file_isolated(self):
        output_df, sampling = calibrate(missing_bp_xml_plain_file, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)


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
        converters = dict([(column, lambda x: str_to_array(x)) for column in array_columns])
        df = pd.read_csv(with_missing_bp_csv_file, converters=converters)
        output_df, sampling = calibrate(df, save_file=False)
        pdt.assert_frame_equal(output_df, with_missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_array_dataframe_isolated(self):
        # Convert columns in the dataframe to arrays (but not to matrices)
        array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficients',
                         'rp_coefficient_errors', 'rp_coefficient_correlations']
        converters = dict([(column, lambda x: str_to_array(x)) for column in array_columns])
        df = pd.read_csv(missing_bp_csv_file, converters=converters)
        output_df, sampling = calibrate(df, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_parsed_dataframe(self):
        # Test completely parsed (arrays + matrices) dataframe
        df, _ = InputReader(with_missing_bp_csv_file, calibrate).read()
        output_df, sampling = calibrate(df, save_file=False)
        pdt.assert_frame_equal(output_df, with_missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_parsed_dataframe_isolated(self):
        # Test completely parsed (arrays + matrices) dataframe
        df, _ = InputReader(missing_bp_csv_file, calibrate).read()
        output_df, sampling = calibrate(df, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)
