from numpy import ndarray
from pandas import isnull
from .dataframe_numpy_array_reader import DataFrameNumPyArrayReader
from .dataframe_string_array_reader import DataFrameStringArrayReader
from gaiaxpy.core import array_to_symmetric_matrix

matrix_columns = [('bp_n_parameters', 'bp_coefficient_correlations'),
                  ('rp_n_parameters', 'rp_coefficient_correlations')]


def extremes_are_enclosing(first_row, column):
    if first_row[column][0] == '[' and first_row[column][-1] == ']':
        return True
    elif first_row[column][0] == '(' and first_row[column][-1] == ')':
        return True
    else:
        return False


def needs_matrix_conversion(array_columns):
    columns_to_matrix = [column for value, column in matrix_columns]
    return set(columns_to_matrix).issubset(set(array_columns))


class DataFrameReader(object):

    def __init__(self, content):
        self.content = content.copy()

    def _read_df(self):
        content = self.content
        columns = content.columns
        first_row = content.iloc[0]
        str_array_columns = [column for column in columns if isinstance(first_row[column], str)
                         and extremes_are_enclosing(first_row, column)]
        np_array_columns = [column for column in columns if isinstance(first_row[column], ndarray)]
        if str_array_columns:
            # Call string reader
            data = DataFrameStringArrayReader(content, str_array_columns)._parse()
            array_columns = str_array_columns
        elif np_array_columns:
            data = DataFrameNumPyArrayReader(content, np_array_columns)._parse()
            array_columns = np_array_columns
        # Nothing to parse
        else:
            data = content
            array_columns = []
        if needs_matrix_conversion(array_columns):
            for index, row in data.iterrows():
                for size_column, values_column in matrix_columns:
                    try:
                        data[values_column][index] = array_to_symmetric_matrix(
                            data[size_column][index].astype(int), row[values_column])
                    except AttributeError as err:
                        if isnull(data[size_column][index]):
                            continue
        return data, None  # No extension for dataframes
