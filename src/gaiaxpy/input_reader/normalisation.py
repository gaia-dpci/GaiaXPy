"""Use consistent array and missing-value representations across input formats."""

import numpy as np
import pandas as pd

from gaiaxpy.core.generic_functions import str_to_array, get_function_name

_CONTINUOUS_ARRAY_COLUMNS = {
    'bp_coefficients', 'rp_coefficients',
    'bp_coefficient_errors', 'rp_coefficient_errors',
    'bp_coefficient_correlations', 'rp_coefficient_correlations',
    'bp_coefficient_covariances', 'rp_coefficient_covariances',
    'bp_covariance_matrix', 'rp_covariance_matrix'
}

_CONTINUOUS_FUNCTIONS = {
    '_apply_colour_equation', '_apply_error_correction',
    '_calibrate', 'calibrate', '_convert', 'convert', '_generate', 'generate',
    'get_inverse_covariance_matrix', 'get_inverse_square_root_covariance_matrix'
}


def get_array_columns(function) -> set[str]:
    """Return the recognised array-field names for an operation.

    Args:
        function (str or callable): GaiaXPy operation.

    Returns:
        set[str]: The configured continuous array columns,
        or an empty set for an operation without a configured group.
    """
    function_name = get_function_name(function)
    if function_name in _CONTINUOUS_FUNCTIONS:
        return _CONTINUOUS_ARRAY_COLUMNS
    return set()


def _is_missing_scalar(value) -> bool:
    """Recognise scalar missing values without testing whole arrays for truth."""
    if value is None or value is pd.NA or isinstance(value, np.ma.core.MaskedConstant):
        return True
    if np.isscalar(value) and not isinstance(value, str):
        try:
            return bool(pd.isna(value))
        except (TypeError, ValueError):
            return False
    return False


def normalise_array_value(value):
    """Convert one array cell to the representation used by the readers.

    Args:
        value (object): Array cell from a file or DataFrame.

    Returns:
        object: A NumPy array for populated list, tuple, array or supported
        bracketed-text values. Missing scalars, blank strings, empty arrays and
        fully masked arrays become np.nan. Partially masked arrays become
        floating-point arrays with NaN at masked positions. Other values pass
        through unchanged.

    Notes:
        Scalar floating-point zero is treated as a missing array for
        compatibility with older Astropy table conversions. Literal strings
        that are not recognised as arrays are retained.
    """
    if _is_missing_scalar(value):
        return np.nan

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return np.nan
        if len(stripped) >= 2 and stripped[0] in '([' and stripped[-1] in ')]':
            value = str_to_array(stripped)
        else:
            return value

    if isinstance(value, np.ma.MaskedArray):
        if value.size == 0 or np.all(np.ma.getmaskarray(value)):
            return np.nan
        if np.any(np.ma.getmaskarray(value)):
            value = value.astype(float).filled(np.nan)
        else:
            value = np.ma.getdata(value)

    if isinstance(value, (list, tuple, np.ndarray)):
        array = np.asarray(value)
        return np.nan if array.size == 0 else array

    # Some Astropy representations historically used 0.0 for a missing
    # array-valued cell. It cannot be a valid value for an array column.
    if isinstance(value, (float, np.floating)) and value == 0.0:
        return np.nan

    return value


def normalise_input_data(data: pd.DataFrame, function) -> pd.DataFrame:
    """Normalise recognised array columns in place.

    Args:
        data (pandas.DataFrame): Table to update.
        function (str or callable): Operation used to identify array columns.

    Returns:
        pandas.DataFrame: The same DataFrame, with present array columns
        converted using normalise_array_value. Other columns are retained.
    """
    array_columns = get_array_columns(function)
    for column in array_columns.intersection(data.columns):
        data[column] = data[column].map(normalise_array_value)
    return data
