from os.path import isabs, isfile
from pathlib import Path

import pandas as pd

from .dataframe_reader import DataFrameReader
from .file_reader import FileParserSelector, FileReader
from .list_reader import ListReader
from .query_reader import QueryReader

default_extension = 'csv'


class InputReader(object):

    def __init__(self, content, function, disable_info=False, user=None, password=None):
        self.content = content
        self.function = function
        self.disable_info = disable_info
        self.user = user
        self.password = password

    def read(self):
        content = self.content
        function = self.function
        user = self.user
        password = self.password
        disable_info = self.disable_info
        if isinstance(content, pd.DataFrame):
            parsed_data, extension = DataFrameReader(content, function, disable_info=disable_info).read_df()
        elif isinstance(content, list):
            parsed_data, extension = ListReader(content, function, user, password, disable_info=disable_info).read()
        elif isinstance(content, Path) or (isinstance(content, str) and isfile(content)):
            parser = FileParserSelector(function)
            parsed_data, extension = FileReader(parser).read(content, disable_info=disable_info)
        elif isinstance(content, str) and content.lower().startswith('select'):
            parsed_data, extension = QueryReader(content, function, user=user, password=password,
                                                 disable_info=disable_info).read()
        else:
            raise ValueError('The input provided does not match any of the expected input types.')
        extension = default_extension if extension is None else extension
        # Deal with some differences in output formats (TODO: move casting to readers)
        parsed_data['source_id'] = parsed_data['source_id'].astype('int64')
        return parsed_data, extension
