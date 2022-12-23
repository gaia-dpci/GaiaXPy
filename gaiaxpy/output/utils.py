import pandas as pd
from numpy import ndarray


def pandas_from_records(lst):
    return pd.DataFrame.from_records([record.to_dict_func for record in lst])


def _array_to_standard(array):
    """
    Converts an array to a tuple so that its string representation corresponds to the archive standard where a list is
        represented using parentheses and commas, i.e.: "(elem1, elem2)".

    Args:
        array (ndarray): An array of floats.

    Returns:
        tuple: The array converted to a tuple.
    """
    return tuple(array)


def _get_array_columns(df):
    return [column for column in df.columns if isinstance(df[column].iloc[0], ndarray)]


def _get_sampling_dict(positions):
    return {'pos': _array_to_standard(positions)}
