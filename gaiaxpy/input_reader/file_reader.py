from os.path import splitext

from gaiaxpy.core.generic_functions import standardise_extension
from gaiaxpy.core.input_validator import check_column_overwrite
from gaiaxpy.file_parser.parse_external import ExternalParser
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS, COV_INPUT_COLUMNS


def external():
    return ExternalParser()


def internal_continuous(requested_columns=None, additional_columns=None):
    return InternalContinuousParser(requested_columns=requested_columns, additional_columns=additional_columns)


def raise_error():
    raise ValueError('File parser not implemented. This function cannot receive a file as input.')


covariance_extensions = ['avro']

function_parser_dict = {'apply_colour_equation': raise_error,
                        'convert': internal_continuous,
                        '_calibrate': internal_continuous,
                        'calibrate': internal_continuous,
                        '_generate': internal_continuous,
                        'generate': internal_continuous,
                        'get_inverse_covariance_matrix': internal_continuous,
                        'get_inverse_square_root_covariance_matrix': internal_continuous,
                        'simulate_continuous': external,
                        'simulate_sampled': external}


class FileReader(object):

    def __init__(self, file_parser_selector, file, additional_columns=None, disable_info=False):
        self.fps = file_parser_selector
        self.file = file
        self.file_extension = standardise_extension(splitext(self.file)[1])
        self.additional_columns = dict() if additional_columns is None else additional_columns
        self.disable_info = disable_info
        mandatory_columns = MANDATORY_INPUT_COLS.get(self.fps.function_name, list())
        style_columns = list()
        if mandatory_columns:
            # Files can contain covariances or correlations depending on the extension
            style_columns = COV_INPUT_COLUMNS if self.file_extension in covariance_extensions else CORR_INPUT_COLUMNS
        self.required_columns = mandatory_columns + style_columns
        self.requested_columns = self.required_columns
        if self.additional_columns:
            check_column_overwrite(additional_columns, self.required_columns)
            self.requested_columns = self.required_columns + self.get_extra_columns_from_extension()

    def read(self):
        # Propagate additional columns
        return self.fps.parser(requested_columns=self.requested_columns,
                               additional_columns=self.additional_columns).parse_file(
            self.file, disable_info=self.disable_info)

    def get_extra_columns_from_extension(self):
        if self.file_extension == 'avro':
            return [c for c in self.additional_columns.keys() if c not in self.required_columns]
        else:
            # Verify columns
            for value in self.additional_columns.values():
                if not isinstance(value, list) or len(value) != 1:
                    if not value[0]:
                        raise ValueError('Empty values are not allowed in additional columns argument.')
                    else:
                        raise ValueError('Column lists longer than one are not allowed in non-nested formats.')
            return [self.additional_columns[c][0] for c in self.additional_columns.keys() if c not in
                    self.required_columns]


class FileParserSelector(object):

    def __init__(self, function):
        self.function_name = function.__name__
        self.mandatory_columns = MANDATORY_INPUT_COLS.get(self.function_name, list())
        self.parser = function_parser_dict[self.function_name]
