import numpy as np
import pandas as pd

from gaiaxpy.core.generic_functions import str_to_array

# Avoid warning, false positive
pd.options.mode.chained_assignment = None


class DataFrameStringArrayReader(object):

    def __init__(self, content, array_columns):
        self.content = content.copy()
        self.array_columns = array_columns

    def _parse_parenthesis_arrays(self):
        df = self.content
        array_columns = self.array_columns
        for column in array_columns:
            df[column] = df[column].apply(lambda x: str_to_array(x))
        return df

    def _parse_brackets_arrays(self):
        df = self.content
        array_columns = self.array_columns
        for column in array_columns:
            df[column] = df[column].map(np.array)
        return df

    def _parse(self):
        def __get_enclosing_element(df, _array_columns):
            # Get enclosing symbol for string arrays, i.e. '(' or '['
            for index, row in df.iterrows():
                for column in _array_columns:
                    if isinstance(row[column], str):
                        if row[column][0] in ['(', '[']:
                            return row[column][0]
                    else:
                        continue

        df = self.content
        array_columns = self.array_columns
        enclosing = __get_enclosing_element(df, array_columns)
        if enclosing == '(':
            df = self._parse_parenthesis_arrays()
        elif enclosing == '[':
            df = self._parse_brackets_arrays()
        return df
