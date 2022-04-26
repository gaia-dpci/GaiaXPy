

class DataFrameNumPyArrayReader(object):

    def __init__(self, content, array_columns):
        self.content = content.copy()
        self.array_columns = array_columns

    def _parse(self):
        df = self.content
        return df
