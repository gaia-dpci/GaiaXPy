from os.path import isfile
from pathlib import Path

import pandas as pd

from .dataframe_reader import DataFrameReader
from .file_reader import FileParserSelector, FileReader
from .list_reader import ListReader
from .required_columns import MANDATORY_INPUT_COLS, COV_INPUT_COLUMNS, CORR_INPUT_COLUMNS
from .query_reader import QueryReader
from ..core.generic_functions import format_additional_columns
from ..core.input_validator import validate_required_columns

default_extension = 'csv'


class InputReader(object):

    def __init__(self, content, function, additional_columns=None, disable_info=False, user=None, password=None):
        if additional_columns is None:
            additional_columns = dict()
        self.content = content
        self.function = function
        self.additional_columns = additional_columns
        if not isinstance(self.additional_columns, dict):
            raise ValueError(f'Additional columns is {type(self.additional_columns)}.')
        self.disable_info = disable_info
        self.user = user
        self.password = password

    def read(self):
        content = self.content
        function = self.function
        disable_info = self.disable_info
        additional_columns = self.additional_columns
        # Input data directly provided by the user
        if isinstance(content, pd.DataFrame):
            reader = DataFrameReader(content, function, additional_columns=additional_columns,
                                     disable_info=disable_info)
        elif isinstance(content, Path) or (isinstance(content, str) and isfile(content)):
            parser = FileParserSelector(function)
            reader = FileReader(parser, content, additional_columns=additional_columns, disable_info=disable_info)
        # Actual input data got from the Archive
        elif isinstance(content, list):
            reader = ListReader(content, function, user=self.user, password=self.password,
                                additional_columns=additional_columns, disable_info=disable_info)
        elif isinstance(content, str) and content.lower().startswith('select'):
            reader = QueryReader(content, function, user=self.user, password=self.password,
                                 additional_columns=additional_columns, disable_info=disable_info)
        else:
            raise ValueError('The input provided does not match any of the expected input types.')
        parsed_data, extension = reader.read()
        parsed_data_columns = parsed_data.columns
        validate_required_columns(parsed_data_columns, reader.requested_columns)
        extension = default_extension if extension is None else extension
        # Deal with some differences in output formats (TODO: move casting to readers)
        parsed_data['source_id'] = parsed_data['source_id'].astype('int64')
        return parsed_data, extension
