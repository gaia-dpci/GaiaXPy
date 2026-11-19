import pandas as pd
import pytest

from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.required_columns import CORR_INPUT_COLUMNS, COV_INPUT_COLUMNS, MANDATORY_INPUT_COLS
from tests.files.continuous import dr3_with_missing_bp_csv_file, dr3_mean_spectra_avro_file

# Covariance columns are auto-generated
__BASE_COLUMNS = set(
    MANDATORY_INPUT_COLS['calibrate'] + ['solution_id', 'bp_covariance_matrix', 'rp_covariance_matrix'])


def test_read_corr_df():
    input_df, _, _ = InputReader(dr3_with_missing_bp_csv_file, generate, truncation=False, release=RELEASES.dr3).read()
    assert_input_can_be_read(input_df, CORR_INPUT_COLUMNS)
    # This should NOT work
    input_df = input_df.drop(columns=['bp_coefficient_errors'])
    with pytest.raises(ValueError):
        _ = generate(input_df, photometric_system=PhotometricSystem.DR3_JKC, save_file=False)


def test_read_cov_df():
    input_df, _, _ = InputReader(dr3_mean_spectra_avro_file, generate, truncation=False, release=RELEASES.dr3).read()
    assert_input_can_be_read(input_df, COV_INPUT_COLUMNS)
    # This should NOT work
    input_df = input_df.drop(columns=['bp_coefficient_covariances'])
    with pytest.raises(ValueError):
        _ = generate(input_df, photometric_system=PhotometricSystem.DR3_JKC, save_file=False)


def assert_input_can_be_read(input_df, style_columns):
    assert set(input_df.columns) == __BASE_COLUMNS.union(set(style_columns))
    # This should work
    output = generate(input_df, photometric_system=PhotometricSystem.DR3_JKC, save_file=False)
    assert isinstance(output, pd.DataFrame)
