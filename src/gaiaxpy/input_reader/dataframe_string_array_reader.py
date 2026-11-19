"""Handle the fallback array conversions used by DataFrameReader.

Recognised spectrum array fields are handled by normalisation instead.
"""

import numpy as np

from gaiaxpy.core.generic_functions import str_to_array


class DataFrameStringArrayReader:
    """Apply the fallback array conversion to a copy of the input DataFrame."""

    def __init__(self, content, array_columns):
        """Copy content and store the array-column names to process."""
        self.content = content.copy()
        self.array_columns = array_columns

    def _parse_parenthesis_arrays(self):
        """Parse cells in the selected columns using str_to_array."""
        df = self.content
        array_columns = self.array_columns
        for column in array_columns:
            df[column] = df[column].apply(lambda x: str_to_array(x))
        return df

    def _parse_brackets_arrays(self):
        """Wrap cells in the selected columns with numpy.array.

        This helper does not parse bracketed text into numeric values.
        """
        df = self.content
        array_columns = self.array_columns
        for column in array_columns:
            df[column] = df[column].map(np.array)
        return df

    def read(self):
        """Choose a fallback conversion using the first row's string cells.

        Returns:
            pandas.DataFrame: The reader's copy. Parenthesised cells use
            str_to_array; square-bracket cells use numpy.array. If no enclosing
            character is found, the copy is returned without conversion.
        """

        def __get_enclosing_element(_df, _array_columns):
            """Find the first string cell's opening bracket in the first row, if any."""
            for row in _df.to_dict('records'):
                for column in _array_columns:
                    if isinstance(row[column], str):
                        if row[column][0] in ['(', '[']:
                            return row[column][0]
                        return None
                    else:
                        continue
                return None
            return None

        df = self.content
        array_columns = self.array_columns
        enclosing = __get_enclosing_element(df, array_columns)
        if enclosing == '(':
            df = self._parse_parenthesis_arrays()
        elif enclosing == '[':
            df = self._parse_brackets_arrays()
        return df
