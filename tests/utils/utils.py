import json
from os.path import basename, isfile

import numpy as np
import pandas as pd

from gaiaxpy.core.generic_functions import str_to_array, array_to_symmetric_matrix
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS

dr3_missing_bp_source_id = 5405570973190252288

_rtol, _atol = 1e-7, 1e-7


def cast_nans(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cast nans to None to avoid pandas FutureWarnings not relevant to the package.
    None does not present comparison issues unlike nan (nan != nan).

    Args:
        df (pd.DataFrame): A pandas DataFrame.

    Returns:
        DataFrame: DataFrame with replaced nan values.
    """
    for col in df.columns:
        df[col] = df[col].replace([float('nan'), np.nan, pd.NA], None)
    return df


def parse_matrices(string):
    return None if len(string) == 0 else np.array(json.loads(string))


def get_spectrum_with_source_id(source_id, spectra):
    if isinstance(spectra, list):
        for spectrum in spectra:
            if spectrum.get_source_id() == source_id:
                return spectrum
    elif isinstance(spectra, pd.DataFrame):
        return spectra.loc[spectra['source_id'] == source_id].to_dict('records')[0]
    raise ValueError('Spectrum does not exist or function is not defined for variable spectra type.')


def pos_file_to_array(pos_file):
    df = pd.read_csv(pos_file, converters={'pos': (lambda x: str_to_array(x))}, **CSV_FLOAT_PRECISION_KWARGS)
    return df['pos'].iloc[0]


def npt_array_err_message(_input):
    msg = f'Array not equal for input file {basename(_input)}.' if isfile(_input) \
        else f'Array not equal for input {_input}.'
    return msg


def is_instance_err_message(_input, instance, band=None):
    instance = instance if isinstance(instance, str) else instance.__name__
    msg = f'Output generated from file {basename(_input)}' if isfile(_input) else f'Input {_input}'
    if isinstance(band, str):
        msg += msg + f' and band {band}'
    msg += f' is not an instance of {instance}.'
    return msg


def assert_band_err(band):
    return f'Assertion failed for band {band}.'


def parse_dfs_for_test(from_file_df, read_input, additional_columns,
                       expected_columns):
    def __parse_df(_df):
        str_cols = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations',
                    'rp_coefficients', 'rp_coefficient_errors', 'rp_coefficient_correlations']
        for col in str_cols:
            _df[col] = _df[col].apply(str_to_array)
        for col in ['bp_coefficient_correlations', 'rp_coefficient_correlations']:
            _df[col] = _df[col].apply(lambda x: array_to_symmetric_matrix(x, 55))
        return _df

    df = __parse_df(from_file_df)
    expected_df = df[expected_columns + [c for c in additional_columns if c not in expected_columns]]
    filtered_read_input = read_input.drop(columns=['bp_covariance_matrix', 'rp_covariance_matrix'])
    return expected_df, filtered_read_input


def assert_dfs_equal(actual: pd.DataFrame, expected: pd.DataFrame, *, rtol: float = 1e-7,
                     atol: float = 1e-7) -> None:
    pd.testing.assert_index_equal(actual.index, expected.index)
    pd.testing.assert_index_equal(actual.columns, expected.columns)

    differences = []

    for row_index in actual.index:
        for column in actual.columns:
            actual_value = actual.at[row_index, column]
            expected_value = expected.at[row_index, column]

            # Handle missing scalar values, including None and NaN.
            actual_missing = (actual_value is None or np.isscalar(actual_value) and
                              pd.isna(actual_value))
            expected_missing = (expected_value is None or np.isscalar(expected_value) and
                                pd.isna(expected_value))

            if actual_missing or expected_missing:
                if actual_missing != expected_missing:
                    differences.append(f"row={row_index!r}, column={column!r}: "
                                       f"actual={actual_value!r}, expected={expected_value!r}")
                continue

            # Handle array-like cells such as flux and flux_error.
            if isinstance(actual_value, (list, tuple, np.ndarray)):
                actual_array = np.asarray(actual_value)
                expected_array = np.asarray(expected_value)

                if actual_array.shape != expected_array.shape:
                    differences.append(f"row={row_index!r}, column={column!r}: "
                                       f"shape differs: actual={actual_array.shape}, "
                                       f"expected={expected_array.shape}")
                    continue

                close = np.isclose(actual_array, expected_array, rtol=rtol, atol=atol,
                                   equal_nan=True)

                for position in np.argwhere(~close):
                    position = tuple(position)
                    actual_element = actual_array[position]
                    expected_element = expected_array[position]

                    absolute_difference = abs(actual_element - expected_element)
                    tolerance = atol + rtol * abs(expected_element)

                    differences.append(
                        f"row={row_index!r}, column={column!r}, "
                        f"position={position}: "
                        f"actual={actual_element!r}, "
                        f"expected={expected_element!r}, "
                        f"abs_diff={absolute_difference:.12g}, "
                        f"allowed={tolerance:.12g}"
                    )

                continue

            # Handle ordinary scalar values.
            if isinstance(actual_value, (float, np.floating)):
                equal = np.isclose(actual_value, expected_value, rtol=rtol, atol=atol,
                                   equal_nan=True)
            else:
                equal = actual_value == expected_value

            if not equal:
                differences.append(f"row={row_index!r}, column={column!r}: "
                                   f"actual={actual_value!r}, expected={expected_value!r}")

    if differences:
        preview = "\n".join(differences[:20])
        remaining = len(differences) - 20

        if remaining > 0:
            preview += f"\n... and {remaining} more differences"

        raise AssertionError(f"DataFrames differ in {len(differences)} value(s):\n{preview}")
