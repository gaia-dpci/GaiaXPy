import numpy.testing as npt
import pandas.testing as pdt
import pytest

from gaiaxpy import calibrate
from tests.test_calibrator.calibrator_solutions import (solution_default_df, sol_with_missing_sampling_array,
                                                        sol_default_sampling_array, with_missing_solution_df,
                                                        missing_solution_df)
from tests.utils.utils import missing_bp_source_id

_atol, _rtol = 1e-10, 1e-10


@pytest.mark.archive
def test_single_element_query():
    src = 5853498713190525696
    query = f'SELECT * FROM gaiadr3.gaia_source WHERE source_id={src}'
    output_df, sampling = calibrate(query, save_file=False)
    source_data_output = output_df[output_df['source_id'] == src]
    source_data_solution = solution_default_df[solution_default_df['source_id'] == src]
    pdt.assert_frame_equal(source_data_output, source_data_solution, atol=_atol, rtol=_rtol)
    npt.assert_array_equal(sampling, sol_default_sampling_array)


@pytest.mark.archive
@pytest.mark.parametrize('input_data',
                         [f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ({missing_bp_source_id})",
                          [missing_bp_source_id]])
def test_missing_bp_isolated(input_data):
    output_df, sampling = calibrate(input_data, save_file=False)
    pdt.assert_frame_equal(output_df, missing_solution_df, check_dtype=False, atol=_atol, rtol=_rtol)
    npt.assert_array_equal(sampling, sol_with_missing_sampling_array)


@pytest.mark.archive
@pytest.mark.parametrize('input_data', ["SELECT * FROM gaiadr3.gaia_source WHERE source_id IN "
                                        f"('5853498713190525696', {missing_bp_source_id}, '5762406957886626816')",
                                        ['5853498713190525696', str(missing_bp_source_id), '5762406957886626816']])
def test_missing_bp_query(input_data):
    output_df, sampling = calibrate(input_data, save_file=False)
    sorted_output_df = output_df.sort_values('source_id', ignore_index=True)
    sorted_solution_df = with_missing_solution_df.sort_values('source_id', ignore_index=True)
    pdt.assert_frame_equal(sorted_output_df, sorted_solution_df, atol=_atol, rtol=_rtol)
    npt.assert_array_equal(sampling, sol_with_missing_sampling_array)
