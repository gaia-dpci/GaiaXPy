class DataFrameNumPyArrayReader(object):

    def __init__(self, content, array_columns):
        self.content = content
        self.array_columns = array_columns

    def read(self):
        df = self.content
        return df
