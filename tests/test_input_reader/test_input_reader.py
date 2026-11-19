from uuid import uuid4

import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import convert
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from tests.files.continuous import dr3_mean_spectra_csv_file

columns_to_read = MANDATORY_INPUT_COLS['convert'] + CORR_INPUT_COLUMNS
dataframe_str = pd.read_csv(dr3_mean_spectra_csv_file, usecols=columns_to_read, **CSV_FLOAT_PRECISION_KWARGS)
parser = InternalContinuousParser(columns_to_read)
dataframe_np, _ = parser.parse_file(dr3_mean_spectra_csv_file)
# Opt for removing cov matrices before comparing. Covariance matrix is tested in a separate file.
dataframe_np = dataframe_np.drop(columns=['bp_covariance_matrix', 'rp_covariance_matrix'])

_rtol, _atol = 1e-24, 1e-24


def test_dfs_dr3():
    # Input correction has no effect on DR3 data
    parsed_df_str, _, _ = InputReader(dataframe_str, convert, truncation=False, release=RELEASES.dr3).read()
    parsed_df_np, _, _ = InputReader(dataframe_np, convert, truncation=False, release=RELEASES.dr3).read()
    pdt.assert_frame_equal(parsed_df_str, parsed_df_np, rtol=_rtol, atol=_atol)


def test_empty_list():
    with pytest.raises(ValueError):
        _ = InputReader([], convert, truncation=False).read()


def test_file_does_not_exist():
    # Generate a unique file name that's unlikely to exist
    fake_path = f'/tmp/testfile_{uuid4()}.txt'
    with pytest.raises(FileNotFoundError):
        _ = InputReader(fake_path, convert, truncation=False).read()
