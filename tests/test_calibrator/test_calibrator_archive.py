import unittest

import numpy.testing as npt
import pandas.testing as pdt

from gaiaxpy import calibrate
from tests.test_calibrator.calibrator_solutions import solution_default_df, sol_with_missing_sampling_array, \
    sol_default_sampling_array, with_missing_solution_df, missing_solution_df
from tests.utils.utils import missing_bp_source_id

_rtol = 1e-10
_atol = 1e-10


class TestCalibratorSingleElement(unittest.TestCase):

    def test_single_element_query(self):
        query = "SELECT * FROM gaiadr3.gaia_source WHERE source_id='5853498713190525696'"
        output_df, sampling = calibrate(query, save_file=False)
        source_data_output = output_df[output_df['source_id'] == 5853498713190525696]
        source_data_solution = solution_default_df[solution_default_df['source_id'] == 5853498713190525696]
        pdt.assert_frame_equal(source_data_output, source_data_solution, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_default_sampling_array)


class TestCalibratorMissingBPQueryInput(unittest.TestCase):

    def test_missing_bp_query(self):
        query = f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5853498713190525696', " \
                f"{missing_bp_source_id}, '5762406957886626816')"
        output_df, sampling = calibrate(query, save_file=False)
        sorted_output_df = output_df.sort_values('source_id', ignore_index=True)
        sorted_solution_df = with_missing_solution_df.sort_values('source_id', ignore_index=True)
        pdt.assert_frame_equal(sorted_output_df, sorted_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_query_isolated(self):
        query = f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ({missing_bp_source_id})"
        output_df, sampling = calibrate(query, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)


class TestCalibratorMissingBPListInput(unittest.TestCase):

    def test_missing_bp_list(self):
        src_list = ['5853498713190525696', str(missing_bp_source_id), '5762406957886626816']
        output_df, sampling = calibrate(src_list, save_file=False)
        sorted_output_df = output_df.sort_values('source_id', ignore_index=True)
        sorted_solution_df = with_missing_solution_df.sort_values('source_id', ignore_index=True)
        pdt.assert_frame_equal(sorted_output_df, sorted_solution_df, check_dtype=False, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)

    def test_missing_bp_isolated(self):
        src_list = [missing_bp_source_id]
        output_df, sampling = calibrate(src_list, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, check_dtype=False, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sol_with_missing_sampling_array)
