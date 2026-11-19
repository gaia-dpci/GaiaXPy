"""Pass through DataFrames whose array cells already contain NumPy arrays."""


class DataFrameNumPyArrayReader:
    """Retain already-parsed array cells without copying or converting the table."""

    def __init__(self, content, array_columns):
        """Store the DataFrame and array-column names supplied by DataFrameReader."""
        self.content = content
        self.array_columns = array_columns

    def read(self):
        """Return the original DataFrame object without modifying it."""
        df = self.content
        return df
