from os.path import isfile
from pathlib import Path

import pandas as pd

from .dataframe_reader import DataFrameReader
from .file_reader import FileParserSelector, FileReader
from .list_reader import ListReader
from .required_columns import MANDATORY_COLS, COVARIANCE_COLUMNS, CORRELATIONS_COLUMNS
from .query_reader import QueryReader
from ..core.input_validator import validate_required_columns

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
        disable_info = self.disable_info
        # Input data directly provided by the user
        if isinstance(content, pd.DataFrame):
            reader = DataFrameReader(content, function, disable_info=disable_info)
        elif isinstance(content, Path) or (isinstance(content, str) and isfile(content)):
            parser = FileParserSelector(function)
            reader = FileReader(parser, content, disable_info=disable_info)
        # Actual input data got from the Archive
        elif isinstance(content, list):
            reader = ListReader(content, function, self.user, self.password, disable_info=disable_info)
        elif isinstance(content, str) and content.lower().startswith('select'):
            reader = QueryReader(content, function, user=self.user, password=self.password, disable_info=disable_info)
        else:
            raise ValueError('The input provided does not match any of the expected input types.')
        parsed_data, extension = reader.read()
        parsed_data_columns = parsed_data.columns
        validate_required_columns(parsed_data_columns, reader.required_columns)
        extension = default_extension if extension is None else extension
        # Deal with some differences in output formats (TODO: move casting to readers)
        parsed_data['source_id'] = parsed_data['source_id'].astype('int64')
        return parsed_data, extension
