from os.path import isfile
from pathlib import Path

import pandas as pd

from .dataframe_reader import DataFrameReader
from .file_reader import FileParserSelector
from .hdfs_reader import HDFSReader
from .list_reader import ListReader
from .local_file_reader import LocalFileReader
from .query_reader import QueryReader

default_extension = 'csv'


class InputReader(object):

    def __init__(self, content, function, truncation, additional_columns=None, selector=None, disable_info=False,
                 user=None, password=None):
        if additional_columns is None:
            additional_columns = dict()
        self.additional_columns = additional_columns
        if not isinstance(self.additional_columns, dict):
            raise ValueError(f'Additional columns is {type(self.additional_columns)}.')
        self.selector = selector if selector is None else selector
        self.content = content
        self.function = function
        self.truncation = truncation
        self.disable_info = disable_info
        self.user = user
        self.password = password

    def read(self):
        content = self.content
        function = self.function
        truncation = self.truncation
        disable_info = self.disable_info
        additional_columns = self.additional_columns
        selector = self.selector
        # Input data directly provided by the user
        if isinstance(content, pd.DataFrame):
            reader = DataFrameReader(content, function, truncation, additional_columns=additional_columns,
                                     selector=selector, disable_info=disable_info)
        elif (isinstance(content, Path) or isinstance(content, str)) and isfile(content):
            parser = FileParserSelector(function)
            reader = LocalFileReader(parser, content, truncation, additional_columns=additional_columns,
                                     selector=selector, disable_info=disable_info)
        # Actual input data got from the Archive
        elif isinstance(content, list):
            reader = ListReader(content, function, truncation, user=self.user, password=self.password,
                                additional_columns=additional_columns, selector=selector, disable_info=disable_info)
        elif isinstance(content, str) and content.lower().startswith('select'):
            reader = QueryReader(content, function, truncation, user=self.user, password=self.password,
                                 additional_columns=additional_columns, selector=selector, disable_info=disable_info)
        elif isinstance(content, str) and content.lower().startswith('hdfs://'):
            parser = FileParserSelector(function)
            reader = HDFSReader(parser, content, truncation, additional_columns=additional_columns, selector=selector,
                                disable_info=disable_info)
        else:
            raise ValueError('The input provided does not match any of the expected input types.')
        parsed_data, extension = reader.read()
        extension = default_extension if extension is None else extension
        return parsed_data, extension
