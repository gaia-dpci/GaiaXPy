import numpy.testing as npt
import pandas as pd
import pytest

from gaiaxpy import calibrate
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.continuous import (dr3_missing_bp_csv_file, dr3_missing_bp_ecsv_file, dr3_missing_bp_fits_file,
                                    dr3_missing_bp_xml_binary_file, dr3_missing_bp_xml_plain_file,
                                    dr3_with_missing_bp_csv_file, dr3_with_missing_bp_ecsv_file,
                                    dr3_with_missing_bp_fits_file, dr3_with_missing_bp_xml_binary_file,
                                    dr3_with_missing_bp_xml_plain_file)
from tests.reference.calibrator import sol_with_missing_sampling_array, with_missing_solution_df, missing_solution_df
from tests.utils.utils import assert_dfs_equal, npt_array_err_message

_atol, _rtol = 1e-12, 1e-12

cal_with_missing_input_files = [dr3_with_missing_bp_csv_file, dr3_with_missing_bp_ecsv_file,
                                dr3_with_missing_bp_fits_file,
                                dr3_with_missing_bp_xml_binary_file, dr3_with_missing_bp_xml_plain_file]

cal_isolated_missing_input_files = [dr3_missing_bp_csv_file, dr3_missing_bp_ecsv_file, dr3_missing_bp_fits_file,
                                    dr3_missing_bp_xml_binary_file, dr3_missing_bp_xml_plain_file]


@pytest.mark.parametrize('file,solution', [(dr3_with_missing_bp_csv_file, with_missing_solution_df),
                                           (dr3_missing_bp_csv_file, missing_solution_df)])
def test_missing_bp_parsed_dataframe(file, solution):
    df, _, _ = InputReader(file, calibrate, truncation=False, release=RELEASES.dr3).read()
    output_df, sampling = calibrate(df, save_file=False, release=RELEASES.dr3)
    npt.assert_array_equal(sampling, sol_with_missing_sampling_array, err_msg=npt_array_err_message(file))
    assert_dfs_equal(output_df, solution, atol=_atol, rtol=_rtol)


@pytest.mark.parametrize('with_missing_file', cal_with_missing_input_files)
def test_missing_bp_file(with_missing_file):
    output_df, sampling = calibrate(with_missing_file, save_file=False, release=RELEASES.dr3)
    npt.assert_array_equal(sampling, sol_with_missing_sampling_array, err_msg=npt_array_err_message(with_missing_file))
    assert_dfs_equal(output_df, with_missing_solution_df, atol=_atol, rtol=_rtol)


@pytest.mark.parametrize('isolated_missing_file', cal_isolated_missing_input_files)
def test_missing_bp_file_isolated(isolated_missing_file):
    output_df, sampling = calibrate(isolated_missing_file, save_file=False, release=RELEASES.dr3)
    npt.assert_array_equal(sampling, sol_with_missing_sampling_array,
                           err_msg=npt_array_err_message(isolated_missing_file))
    assert_dfs_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)


@pytest.mark.parametrize('input_data,solution', [(dr3_with_missing_bp_csv_file, with_missing_solution_df),
                                                 (dr3_missing_bp_csv_file, missing_solution_df)])
def test_missing_bp_simple_dataframe(input_data, solution):
    df = pd.read_csv(input_data, **CSV_FLOAT_PRECISION_KWARGS)
    output_df, sampling = calibrate(df, save_file=False, release=RELEASES.dr3)
    assert_dfs_equal(output_df, solution, atol=_atol, rtol=_rtol)
    npt.assert_array_equal(sampling, sol_with_missing_sampling_array)


@pytest.mark.parametrize('file,solution', list(zip([dr3_with_missing_bp_csv_file, dr3_missing_bp_csv_file],
                                                   [with_missing_solution_df, missing_solution_df])))
def test_missing_bp_array_dataframe(file, solution):
    # Convert columns in the dataframe to arrays (but not to matrices)
    array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficients',
                     'rp_coefficient_errors', 'rp_coefficient_correlations']
    df = pd.read_csv(file, converters=dict([(column, lambda x: str_to_array(x)) for column in array_columns]),
                     **CSV_FLOAT_PRECISION_KWARGS)
    output_df, sampling = calibrate(df, save_file=False, release=RELEASES.dr3)
    npt.assert_array_equal(sampling, sol_with_missing_sampling_array, err_msg=npt_array_err_message(file))
    assert_dfs_equal(output_df, solution, atol=_atol, rtol=_rtol)
