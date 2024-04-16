from os.path import splitext

from gaiaxpy.core.generic_functions import standardise_extension, cast_output
from gaiaxpy.core.input_validator import check_column_overwrite
from gaiaxpy.file_parser.parse_external import ExternalParser
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, COV_INPUT_COLUMNS, CORR_INPUT_COLUMNS, \
    TRUNCATION_COLS


def external(requested_columns=None, additional_columns=None, selector=None, **kwargs):
    return ExternalParser(requested_columns=requested_columns, additional_columns=additional_columns,
                          selector=selector, **kwargs)


def internal_continuous(requested_columns=None, additional_columns=None, selector=None, **kwargs):
    return InternalContinuousParser(requested_columns=requested_columns, additional_columns=additional_columns,
                                    selector=selector, **kwargs)


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
                        'get_inverse_square_root_covariance_matrix': internal_continuous}


class FileReader:

    def __init__(self, file_parser_selector, file, truncation, additional_columns=None, selector=None,
                 disable_info=False, **kwargs):
        self.fps = file_parser_selector
        self.file = file
        self.file_extension = standardise_extension(splitext(file)[1])
        self.truncation = truncation
        self.additional_columns = dict() if additional_columns is None else additional_columns
        self.selector = selector
        self.disable_info = disable_info
        mandatory_columns = MANDATORY_INPUT_COLS.get(self.fps.function_name, list())
        style_columns = list()
        if mandatory_columns:
            # Files can contain covariances or correlations depending on the extension
            style_columns = COV_INPUT_COLUMNS if self.file_extension in covariance_extensions else CORR_INPUT_COLUMNS
        self.required_columns = mandatory_columns + style_columns
        if truncation:
            self.required_columns = self.required_columns + TRUNCATION_COLS
        self.requested_columns = self.required_columns
        if self.additional_columns:
            check_column_overwrite(additional_columns, self.required_columns)
            self.requested_columns = self.required_columns + self.get_extra_columns_from_extension()
        if kwargs:
            self.address = kwargs.get('address', None)
            self.port = kwargs.get('port', None)

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

    def read(self):
        parser_arguments = {
            'requested_columns': self.requested_columns,
            'additional_columns': self.additional_columns,
            'selector': self.selector
        }
        if hasattr(self, 'address') and hasattr(self, 'port'):
            parser_arguments['address'] = self.address
            parser_arguments['port'] = self.port
        data, extension = self.fps.parser(**parser_arguments).parse_file(self.file, disable_info=self.disable_info)
        return cast_output(data), extension


class FileParserSelector(object):

    def __init__(self, function):
        self.function_name = function.__name__
        self.mandatory_columns = MANDATORY_INPUT_COLS.get(self.function_name, list())
        self.parser = function_parser_dict[self.function_name]
