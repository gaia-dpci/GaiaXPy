import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.core.generic_functions import reverse_simple_add_col_dict, format_additional_columns
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.file_parser.cast import _cast
from tests.files.continuous import dr3_with_missing_bp_csv_file
from tests.files.generator import no_correction_solution_path


@pytest.fixture
def setup_data():
    yield {'df': _cast(pd.read_csv(dr3_with_missing_bp_csv_file, **CSV_FLOAT_PRECISION_KWARGS))}


def test_one_non_required_additional_col_as_list(setup_data):
    df = setup_data['df']
    additional_columns = ['solution_id']
    solution = pd.read_csv(no_correction_solution_path, **CSV_FLOAT_PRECISION_KWARGS)
    solution = solution.drop(columns=[c for c in solution.columns if c != 'source_id' and 'Sdss_' not in c])
    output = generate(df, photometric_system=PhotometricSystem.DR3_SDSS, additional_columns=additional_columns,
                      error_correction=False, save_file=False)
    output = _cast(output)
    assert all(elem in output.columns for elem in additional_columns)
    pdt.assert_frame_equal(output[additional_columns], df[additional_columns])
    output_to_compare = output.drop(columns=additional_columns)
    pdt.assert_frame_equal(output_to_compare, _cast(solution))


def test_more_than_one_non_required_additional_col_as_list(setup_data):
    df = setup_data['df']
    additional_columns = ['solution_id', 'bp_degrees_of_freedom']
    solution = pd.read_csv(no_correction_solution_path, **CSV_FLOAT_PRECISION_KWARGS)
    solution = solution.drop(columns=[c for c in solution.columns if c != 'source_id' and 'Stromgren_' not in c])
    output = generate(df, photometric_system=PhotometricSystem.DR3_Stromgren, additional_columns=additional_columns,
                      error_correction=False, save_file=False)
    assert all(elem in output.columns for elem in additional_columns)
    pdt.assert_frame_equal(output[additional_columns], df[additional_columns])
    output_to_compare = output.drop(columns=additional_columns)
    pdt.assert_frame_equal(output_to_compare, _cast(solution))


def test_one_required_additional_col_as_list(setup_data):
    df = setup_data['df']
    additional_columns = ['source_id']
    solution = pd.read_csv(no_correction_solution_path, **CSV_FLOAT_PRECISION_KWARGS)
    solution = solution.drop(columns=[c for c in solution.columns if c != 'source_id' and 'GaiaVega_' not in c])
    output = generate(df, photometric_system=PhotometricSystem.DR3_Gaia_Vega, additional_columns=additional_columns,
                      error_correction=False, save_file=False)
    assert all(elem in output.columns for elem in additional_columns)
    pdt.assert_frame_equal(output[additional_columns], df[additional_columns])
    output_to_compare = output  # Column is already in the output, it shouldn't be dropped before the comparison
    pdt.assert_frame_equal(output_to_compare, _cast(solution))


def test_one_non_required_additional_col_as_dict(setup_data):
    df = setup_data['df']
    additional_columns = {'solution_id': 'solution_id'}
    additional_columns_values = list(additional_columns.keys())
    solution = pd.read_csv(no_correction_solution_path, **CSV_FLOAT_PRECISION_KWARGS)
    solution = solution.drop(columns=[c for c in solution.columns if c != 'source_id' and 'Sdss_' not in c])
    output = generate(df, photometric_system=PhotometricSystem.DR3_SDSS, additional_columns=additional_columns,
                      error_correction=False, save_file=False)
    assert all(elem in output.columns for elem in additional_columns_values)
    pdt.assert_frame_equal(output[additional_columns_values], df[additional_columns_values])
    output_to_compare = output.drop(columns=additional_columns_values)
    pdt.assert_frame_equal(output_to_compare, _cast(solution))


def test_more_than_one_non_required_additional_col_as_dict(setup_data):
    df = setup_data['df']
    additional_columns = {'dofrp': 'rp_degrees_of_freedom', 'bp_dof': 'bp_degrees_of_freedom'}
    additional_columns_keys = list(additional_columns.keys())
    additional_columns_values = list(additional_columns.values())
    solution = pd.read_csv(no_correction_solution_path, **CSV_FLOAT_PRECISION_KWARGS)
    rename_dict = reverse_simple_add_col_dict(format_additional_columns(additional_columns))
    solution = solution.rename(columns=rename_dict)
    solution = solution[[c for c in solution.columns if c in additional_columns_values or c == 'source_id' or
                         'Stromgren_' in c]]
    output = generate(df, photometric_system=PhotometricSystem.DR3_Stromgren, additional_columns=additional_columns,
                      error_correction=False, save_file=False)
    assert all(elem in output.columns for elem in additional_columns_keys)
    pdt.assert_frame_equal(output[additional_columns_keys], df.rename(columns=rename_dict)[additional_columns_keys])
    output_to_compare = output.drop(columns=additional_columns_keys)
    pdt.assert_frame_equal(output_to_compare, _cast(solution))


def test_rename_mandatory_columns(setup_data):
    additional_columns = {'bp_n_relevant_bases': 'source_id'}
    with pytest.raises(ValueError):
        generate(setup_data['df'], photometric_system=PhotometricSystem.DR3_Stromgren,
                 additional_columns=additional_columns, error_correction=False, save_file=False)
