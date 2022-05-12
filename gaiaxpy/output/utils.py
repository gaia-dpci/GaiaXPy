import pandas as pd
from numpy import ndarray


def pandas_from_records(lst, to_dict_func):
    records_df = pd.DataFrame.from_records(
                 [record.to_dict_func for record in lst])
    return records_df


def _array_to_standard(array):
    """
    Converts an array to a tuple so that its string representation corresponds to
    the archive standard where a list is represented using parentheses and commas,
    i.e.: "(elem1, elem2)".

    Args:
        array (ndarray): An array of floats.

    Returns:
        tuple: The array converted to a tuple.
    """
    return tuple(array)


def _get_array_columns(df):
    """
    TODO: add docstring
    """
    array_columns = []
    for column in df.columns:
        if isinstance(df[column].iloc[0], ndarray):
            array_columns.append(column)
    return array_columns


def _get_sampling_dict(positions):
    return {'pos': _array_to_standard(positions)}
