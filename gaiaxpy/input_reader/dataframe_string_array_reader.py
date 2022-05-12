import numpy as np
import pandas as pd

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
            # String column to NumPy array
            for index, row in df.iterrows():
                df[column][index] = np.fromstring(
                    row[column][1:-1], sep=',')
        return df

    def _parse_brackets_arrays(self):
        df = self.content
        array_columns = self.array_columns
        for column in array_columns:
            # String column to NumPy array
            for index, row in df.iterrows():
                df[column][index] = np.array(row[column])
        return df

    def _parse(self):
        df = self.content
        array_columns = self.array_columns
        # Get enclosing symbol for string arrays, i.e. '(' or '['
        enclosing = df[array_columns[0]].iloc[0][0]
        if enclosing == '(':
            df = self._parse_parenthesis_arrays()
        elif enclosing == '[':
            df = self._parse_brackets_arrays()
        return df
