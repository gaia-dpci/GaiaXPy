import numpy.testing as npt
import pandas as pd
import pytest

from gaiaxpy import convert
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.continuous import (dr3_missing_bp_csv_file, dr3_missing_bp_ecsv_file, dr3_missing_bp_fits_file,
                                    dr3_missing_bp_xml_binary_file, dr3_missing_bp_xml_plain_file,
                                    dr3_with_missing_bp_csv_file, dr3_with_missing_bp_ecsv_file,
                                    dr3_with_missing_bp_fits_file, dr3_with_missing_bp_xml_binary_file,
                                    dr3_with_missing_bp_xml_plain_file)
from tests.reference.converter import with_missing_solution_df, with_missing_solution_sampling, missing_solution_df
from tests.utils.utils import assert_dfs_equal

_rtol, _atol = 1e-7, 1e-7

con_with_missing_input_files = [dr3_with_missing_bp_csv_file, dr3_with_missing_bp_ecsv_file,
                                dr3_with_missing_bp_fits_file,
                                dr3_with_missing_bp_xml_binary_file, dr3_with_missing_bp_xml_plain_file]
con_isolated_missing_input_files = [dr3_missing_bp_csv_file, dr3_missing_bp_ecsv_file, dr3_missing_bp_fits_file,
                                    dr3_missing_bp_xml_binary_file,
                                    dr3_missing_bp_xml_plain_file]


@pytest.mark.parametrize('file', con_with_missing_input_files)
def test_with_missing_bp_file(file):
    output_df, sampling = convert(file, save_file=False, release=RELEASES.dr3)
    npt.assert_array_equal(sampling, with_missing_solution_sampling)
    assert_dfs_equal(output_df, with_missing_solution_df, rtol=_rtol, atol=_atol)


@pytest.mark.parametrize('file', con_isolated_missing_input_files)
def test_missing_bp_file_isolated(file):
    output_df, sampling = convert(file, save_file=False, release=RELEASES.dr3)
    assert_dfs_equal(output_df, missing_solution_df, atol=_atol, rtol=_rtol)
    npt.assert_array_equal(sampling, with_missing_solution_sampling)


@pytest.mark.parametrize('file,solution', [(dr3_with_missing_bp_csv_file, with_missing_solution_df),
                                           (dr3_missing_bp_csv_file, missing_solution_df)])
def test_missing_bp_simple_dataframe(file, solution):
    # Test dataframe containing strings instead of arrays
    df = pd.read_csv(file, **CSV_FLOAT_PRECISION_KWARGS)
    output_df, sampling = convert(df, save_file=False, release=RELEASES.dr3)
    assert_dfs_equal(output_df, solution, rtol=_rtol, atol=_atol)
    npt.assert_array_equal(sampling, with_missing_solution_sampling)


@pytest.mark.parametrize('_input,solution', [(dr3_with_missing_bp_csv_file, with_missing_solution_df),
                                             (dr3_missing_bp_csv_file, missing_solution_df)])
def test_missing_bp_parsed_dataframe(_input, solution):
    dr3 = RELEASES.dr3
    df, _, _ = InputReader(_input, convert, truncation=False, release=dr3).read()
    output_df, sampling = convert(df, save_file=False, release=dr3)
    assert_dfs_equal(output_df, solution, rtol=_rtol, atol=_atol)
    npt.assert_array_equal(sampling, with_missing_solution_sampling)


@pytest.mark.parametrize('_input,solution', [(dr3_with_missing_bp_csv_file, with_missing_solution_df),
                                             (dr3_missing_bp_csv_file, missing_solution_df)])
def test_missing_bp_array_dataframe(_input, solution):
    # Convert columns in the dataframe to arrays (but not to matrices)
    array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficients',
                     'rp_coefficient_errors', 'rp_coefficient_correlations']
    _converters = dict([(column, lambda x: str_to_array(x)) for column in array_columns])
    df = pd.read_csv(_input, converters=_converters, **CSV_FLOAT_PRECISION_KWARGS)
    output_df, sampling = convert(df, save_file=False, release=RELEASES.dr3)
    assert_dfs_equal(output_df, solution, rtol=_rtol, atol=_atol)
    npt.assert_array_equal(sampling, with_missing_solution_sampling)
