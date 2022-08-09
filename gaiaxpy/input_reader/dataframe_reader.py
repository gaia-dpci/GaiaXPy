from numpy import ndarray
from pandas import isnull
from .dataframe_numpy_array_reader import DataFrameNumPyArrayReader
from .dataframe_string_array_reader import DataFrameStringArrayReader
from gaiaxpy.core.generic_functions import array_to_symmetric_matrix

matrix_columns = [('bp_n_parameters', 'bp_coefficient_correlations'),
                  ('rp_n_parameters', 'rp_coefficient_correlations')]


def extremes_are_enclosing(first_row, column):
    left = first_row[column][0]
    right = first_row[column][-1]
    return (left == '[' and right == ']') or (left == '(' and right == ')')


def needs_matrix_conversion(array_columns):
    columns_to_matrix = (column for value, column in matrix_columns)
    return set(columns_to_matrix).intersection(set(array_columns))


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
        else:
            data = content
            array_columns = []
        if needs_matrix_conversion(array_columns):
            for size_column, values_column in matrix_columns:
                    data[values_column] = data.apply(lambda row: \
                     array_to_symmetric_matrix(row[values_column], row[size_column]), \
                    axis=1)
        return data, None  # No extension returned for dataframes
