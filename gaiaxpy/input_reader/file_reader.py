from os.path import splitext

from gaiaxpy.core.generic_functions import standardise_extension, format_additional_columns
from gaiaxpy.file_parser.parse_external import ExternalParser
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS, COV_INPUT_COLUMNS


def external():
    return ExternalParser()


def internal_continuous(required_columns):
    return InternalContinuousParser(required_columns=required_columns)


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
        if additional_columns is None:
            additional_columns = list()
        self.fps = file_parser_selector
        self.file = file
        self.file_extension = standardise_extension(splitext(self.file)[1])
        self.disable_info = disable_info
        mandatory_columns = MANDATORY_INPUT_COLS.get(self.fps.function_name, list())
        style_columns = list()
        if mandatory_columns:
            # Files can contain covariances or correlations depending on the extension
            style_columns = COV_INPUT_COLUMNS if self.file_extension in covariance_extensions else CORR_INPUT_COLUMNS
        self.required_columns = mandatory_columns + style_columns
        additional_columns = format_additional_columns(additional_columns)
        if additional_columns:
            self.required_columns = self.required_columns + [c for c in additional_columns if c not in
                                                             self.required_columns]


    def read(self):
        return self.fps.parser(self.required_columns).parse_file(self.file, disable_info=self.disable_info)


class FileParserSelector(object):

    def __init__(self, function):
        self.function_name = function.__name__
        self.mandatory_columns = MANDATORY_INPUT_COLS.get(self.function_name, list())
        self.parser = function_parser_dict[self.function_name]
