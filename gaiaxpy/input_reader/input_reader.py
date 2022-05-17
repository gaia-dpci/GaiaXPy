import pandas as pd
from os import path
from .dataframe_reader import DataFrameReader
from .file_reader import FileReader
from .list_reader import ListReader
from .query_reader import QueryReader


default_extension = 'csv'


class InputReader(object):

    def __init__(self, content, function, user=None, password=None):
        self.content = content
        self.function = function
        self.user = user
        self.password = password

    def _string_reader(self):
        content = self.content
        function = self.function
        user = self.user
        password = self.password
        # Check whether content is path
        if path.isfile(content) or path.isabs(content):
            selector = FileReader(function)
            parser = selector._select()  # Select type of parser required
            parsed_input_data, extension = parser.parse(content)
        # Query should start with select
        elif content.lower().startswith('select'):
            parsed_input_data, extension = QueryReader(content, function, user, password)._read()
        else:
            raise ValueError('Input string does not correspond to an existing file and it is not an ADQL query.')
        return parsed_input_data, extension

    def _read(self):
        content = self.content
        function = self.function
        user = self.user
        password = self.password
        # DataFrame reader
        if isinstance(content, pd.DataFrame):
            # Call Dataframe reader
            parsed_data, extension = DataFrameReader(content)._read_df()
        # List reader for query
        elif isinstance(content, list):
            # Construct query from list
            parsed_data, extension = ListReader(content, function, user, password)._read()
        # String can be either query or file path
        elif isinstance(content, str):
            parsed_data, extension = self._string_reader()
        else:
            raise ValueError('The input provided does not match any of the expected input types.')
        if extension is None:
            extension = default_extension
        return parsed_data, extension
