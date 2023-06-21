import unittest

import numpy.testing as npt
import pandas.testing as pdt

from gaiaxpy import convert
from tests.test_converter.converter_paths import missing_solution_df, with_missing_solution_df, \
    with_missing_solution_sampling
from tests.utils.utils import missing_bp_source_id

_rtol, _atol = 1e-7, 1e-7


class TestConverterMissingBPQueryInput(unittest.TestCase):

    def test_missing_bp_query(self):
        query = "SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5853498713190525696'," \
                f" {str(missing_bp_source_id)}, '5762406957886626816')"
        output_df, sampling = convert(query, save_file=False)
        sort_columns = ['source_id', 'xp']
        sorted_output_df = output_df.sort_values(by=sort_columns, ignore_index=True)
        sorted_solution_df = with_missing_solution_df.sort_values(by=sort_columns, ignore_index=True)
        pdt.assert_frame_equal(sorted_output_df, sorted_solution_df, rtol=_rtol, atol=_atol)
        npt.assert_array_equal(sampling, with_missing_solution_sampling)

    def test_missing_bp_query_isolated(self):
        query = f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ({missing_bp_source_id})"
        output_df, sampling = convert(query, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, with_missing_solution_sampling)


class TestConverterMissingBPListInput(unittest.TestCase):

    def test_missing_bp_list(self):
        src_list = ['5853498713190525696', str(missing_bp_source_id), '5762406957886626816']
        output_df, sampling = convert(src_list, save_file=False)
        sorted_output_df = output_df.sort_values('source_id', ignore_index=True)
        sorted_solution_df = with_missing_solution_df.sort_values('source_id', ignore_index=True)
        pdt.assert_frame_equal(sorted_output_df, sorted_solution_df, rtol=_rtol, atol=_atol, check_dtype=False)
        npt.assert_array_equal(sampling, with_missing_solution_sampling)

    def test_missing_bp_isolated(self):
        src_list = [missing_bp_source_id]
        output_df, sampling = convert(src_list, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df, check_dtype=False, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, with_missing_solution_sampling)
