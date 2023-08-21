import numpy as np

from gaiaxpy.core.generic_functions import array_to_symmetric_matrix
from .dataframe_numpy_array_reader import DataFrameNumPyArrayReader
from .dataframe_string_array_reader import DataFrameStringArrayReader
from .required_columns import MANDATORY_COLS, COVARIANCE_COLUMNS, CORRELATIONS_COLUMNS
from ..core.satellite import BANDS
from ..spectrum.utils import get_covariance_matrix

covariance_columns = ['bp_covariance_matrix', 'rp_covariance_matrix']
matrix_columns = [('bp_n_parameters', 'bp_coefficient_correlations'),
                  ('rp_n_parameters', 'rp_coefficient_correlations')]


def extremes_are_enclosing(row, column):
    return (row[column][0] == '(' and row[column][-1] == ')') or (row[column][0] == '[' and row[column][-1] == ']')


def needs_matrix_conversion(array_columns):
    columns_to_matrix = (column for value, column in matrix_columns)
    return set(columns_to_matrix).intersection(set(array_columns))


class DataFrameReader(object):

    def __init__(self, content, function, additional_columns=None, disable_info=False):
        additional_columns = [] if additional_columns is None else additional_columns
        self.function_name = function if isinstance(function, str) else function.__name__
        self.content = content.copy()
        self.columns = self.content.columns
        mandatory_columns = MANDATORY_COLS.get(self.function_name, list())
        style_columns = list()
        if mandatory_columns:
            style_columns = COVARIANCE_COLUMNS if all([c in mandatory_columns for c in COVARIANCE_COLUMNS]) \
                else CORRELATIONS_COLUMNS
        self.required_columns = mandatory_columns + style_columns
        if additional_columns:
            self.required_columns = self.required_columns + [c for c in additional_columns if c not in
                                                             self.required_columns]
        self.disable_info = disable_info
        self.info_msg = 'Reading input DataFrame...'

    def __get_parseable_columns(self):
        str_columns, np_columns = [], []
        content = self.content
        rows = content.iloc[0:2]
        rows_dict = rows.to_dict('records')
        for row in rows_dict:
            for column in content.columns:
                if isinstance(row[column], str) and extremes_are_enclosing(row, column):
                    str_columns.append(column)
                if isinstance(row[column], np.ndarray):
                    np_columns.append(column)
        return list(set(str_columns)), list(set(np_columns))

    def read(self):
        if not self.disable_info:
            print(self.info_msg, end='\r')
        content = self.content
        str_array_columns, np_array_columns = self.__get_parseable_columns()
        if str_array_columns:
            data = DataFrameStringArrayReader(content, str_array_columns).read()  # Call string reader
            array_columns = str_array_columns
        elif np_array_columns:
            data = DataFrameNumPyArrayReader(content, np_array_columns).read()
            array_columns = np_array_columns
        else:
            data = content
            array_columns = []
        if needs_matrix_conversion(array_columns):
            for size_column, values_column in matrix_columns:
                data[values_column] = data.apply(lambda row: array_to_symmetric_matrix(row[values_column],
                                                                                       row[size_column]), axis=1)
            if matrix_columns:
                for band in BANDS:
                    data[f'{band}_covariance_matrix'] = data.apply(get_covariance_matrix, axis=1, args=(band,))
                self.required_columns = self.required_columns + covariance_columns
        if not self.disable_info:
            print(self.info_msg + ' Done!', end='\r')
        data_to_return = data[self.required_columns] if self.required_columns else data
        # No extension returned for DataFrames
        return data_to_return, None
