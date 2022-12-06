from gaiaxpy.file_parser.parse_external import ExternalParser
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser


def external():
    return ExternalParser()


def internal_continuous():
    return InternalContinuousParser()


def raise_error():
    raise ValueError('File parser not implemented. This function cannot receive a file as input.')


function_parser_dict = {'apply_colour_equation': raise_error,
                        'convert': internal_continuous,
                        '_calibrate': internal_continuous,
                        'calibrate': internal_continuous,
                        'generate': internal_continuous,
                        'get_inverse_covariance_matrix': internal_continuous}


class FileReader(object):

    def __init__(self, function):
        self.function = function.__name__

    def _select(self):
        return function_parser_dict[self.function]()
