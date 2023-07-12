from os.path import isabs, isfile
from pathlib import Path

import pandas as pd

from .dataframe_reader import DataFrameReader
from .file_reader import FileReader
from .list_reader import ListReader
from .query_reader import QueryReader

default_extension = 'csv'


class InputReader(object):

    def __init__(self, content, function, user=None, password=None, additional_columns=None, disable_info=False):
        self.content = content
        self.function = function
        self.user = user
        self.password = password
        self.disable_info = disable_info
        self.additional_columns = additional_columns

    def __string_reader(self):
        content = self.content
        function = self.function
        user = self.user
        password = self.password
        # Check if content is file path
        if isfile(content) or isabs(content):
            selector = FileReader(function, disable_info=self.disable_info)
            parser = selector.select()  # Select type of parser required
            parsed_input_data, extension = parser._parse(content, additional_columns=self.additional_columns)
        # Query should start with select
        elif content.lower().startswith('select'):
            parsed_input_data, extension = QueryReader(content, function, user=user, password=password,
                                                       disable_info=self.disable_info).read()
        else:
            raise ValueError('Input string does not correspond to an existing file and it is not an ADQL query.')
        return parsed_input_data, extension

    def read(self):
        content = self.content
        function = self.function
        user = self.user
        password = self.password
        if isinstance(content, pd.DataFrame):
            parsed_data, extension = DataFrameReader(content, disable_info=self.disable_info).read_df()
        elif isinstance(content, list):
            parsed_data, extension = ListReader(content, function, user, password,
                                                disable_info=self.disable_info).read()
        # String can be either query or file path
        elif isinstance(content, str):
            parsed_data, extension = self.__string_reader()
        elif isinstance(content, Path):
            self.content = str(content)
            parsed_data, extension = self.__string_reader()
        else:
            raise ValueError('The input provided does not match any of the expected input types.')
        extension = default_extension if extension is None else extension
        # Deal with some differences in output formats (TODO: move casting to readers)
        parsed_data['source_id'] = parsed_data['source_id'].astype('int64')
        return parsed_data, extension
