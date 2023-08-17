from gaiaxpy.file_parser.parse_external import ExternalParser
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.mandatory_columns import MANDATORY_COLS


def external():
    return ExternalParser()


def internal_continuous(mandatory_columns):
    return InternalContinuousParser(mandatory_columns=mandatory_columns)


def raise_error():
    raise ValueError('File parser not implemented. This function cannot receive a file as input.')


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

    def __init__(self, file_parser_selector):
        self.fps = file_parser_selector

    def read(self, file, disable_info):
        return self.fps.parser.parse_file(file, disable_info=disable_info)


class FileParserSelector(object):

    def __init__(self, function):
        self.function = function.__name__
        self.mandatory_columns = MANDATORY_COLS[self.function]
        self.parser = function_parser_dict[self.function](self.mandatory_columns)
