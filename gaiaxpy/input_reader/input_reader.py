import warnings
from os.path import isabs, isfile
from pathlib import Path

import pandas as pd

from .dataframe_reader import DataFrameReader
from .file_reader import FileReader
from .list_reader import ListReader
from .query_reader import QueryReader

default_extension = 'csv'


class InputReader(object):

    def __init__(self, content, function, user=None, password=None, disable_info=False, additional_columns=None):
        self.content = content
        self.function = function
        self.user = user
        self.password = password
        self.disable_info = disable_info
        self.additional_columns = additional_columns if 'generate' in function.__name__ else []
        if ((isinstance(content, Path) or isinstance(content, str)) and not isfile(content)) or\
                (isinstance(self.additional_columns, list) and len(self.additional_columns) == 0):
            warnings.warn('Additional columns were received but this behaviour is currently only implemented for input'
                          ' files and the function generate. Additional columns will be ignored.', stacklevel=2)


    def __string_reader(self):
        content = self.content
        function = self.function
        user = self.user
        password = self.password
        # Check whether content is path
        if isfile(content) or isabs(content):
            selector = FileReader(function, disable_info=self.disable_info)
            parser = selector._select()  # Select type of parser required
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
        # DataFrame reader
        if isinstance(content, pd.DataFrame):
            # Call Dataframe reader
            parsed_data, extension = DataFrameReader(content, disable_info=self.disable_info)._read_df()
        # List reader for query
        elif isinstance(content, list):
            # Construct query from list
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
        parsed_data['source_id'] = parsed_data['source_id'].astype('int64')
        return parsed_data, extension
