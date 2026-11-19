"""Choose file parsers and input columns for GaiaXPy operations."""

from gaiaxpy.core.generic_functions import get_file_extension, cast_output, get_function_name
from gaiaxpy.core.input_validator import check_column_overwrite
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, COV_INPUT_COLUMNS, CORR_INPUT_COLUMNS, \
    TRUNCATION_COLS, requires_coefficient_errors, OPTIONAL_INPUT_COLS, order_input_columns


def internal_continuous(requested_columns=None, additional_columns=None, selector=None, **kwargs):
    """Create a continuous-spectrum parser with the supplied options."""
    return InternalContinuousParser(requested_columns=requested_columns, additional_columns=additional_columns,
                                    selector=selector, **kwargs)


def raise_error(*args, **kwargs):
    """Reject file input for an operation without an implemented file parser."""
    _, _ = args, kwargs
    raise ValueError('File parser not implemented. This function cannot receive a file as input.')


covariance_extensions = ['avro']

function_parser_dict = {'apply_colour_equation': raise_error,
                        'apply_error_correction': raise_error,
                        'convert': internal_continuous,
                        '_calibrate': internal_continuous,
                        'calibrate': internal_continuous,
                        '_generate': internal_continuous,
                        'generate': internal_continuous,
                        'get_inverse_covariance_matrix': internal_continuous,
                        'get_inverse_square_root_covariance_matrix': internal_continuous
                        }


class FileReader:
    """Configure a spectrum parser using the operation and underlying file format.

    Avro coefficient inputs use covariance columns; other formats use errors and
    correlations. Gzip suffixes do not change the underlying format selection.
    Support for reading Avro files is intended solely for internal use; the
    Archive does not distribute files in this format.
    """

    def __init__(self, file_parser_selector, file, truncation, additional_columns=None, selector=None,
                 disable_info=False, **kwargs):
        """Determine required columns and retain options for the selected parser.

        Args:
            file_parser_selector (FileParserSelector): Parser factory and operation.
            file (str or pathlib.Path): Input filename, or HDFS file path when
                connection options are supplied by HDFSReader.
            truncation (bool): Whether subsequent calculations use the recommended
                number of basis functions for each source and photometer. When True,
                this reader includes bp_n_relevant_bases and rp_n_relevant_bases
                for that calculation. When False, calculations use all available
                basis functions.
            additional_columns (dict or None): Mappings from output names to input
                fields. Non-nested formats require a one-element list per mapping;
                Avro mappings may describe nested fields. Support for Avro files is
                intended solely for internal use; the Archive does not distribute
                files in this format.
            selector (object or None): Selection passed to the parser.
            disable_info (bool): Suppress routine reading messages.
            **kwargs: HDFS connection options: address and port.

        Notes:
            Column-name collisions and invalid extra-column mappings can raise
            errors while this reader is being configured. The file is read later.
        """
        self.fps = file_parser_selector
        self.file = file
        self.file_extension = get_file_extension(file)
        self.truncation = truncation
        self.additional_columns = dict() if additional_columns is None else additional_columns
        self.selector = selector
        self.disable_info = disable_info
        mandatory_columns = MANDATORY_INPUT_COLS.get(self.fps.function_name, list())
        style_columns = list()
        if requires_coefficient_errors(self.fps.function_name):
            # Coefficient products can contain covariances or correlations depending on the extension
            style_columns = COV_INPUT_COLUMNS if self.file_extension in covariance_extensions else CORR_INPUT_COLUMNS
        self.required_columns = order_input_columns(mandatory_columns + style_columns)
        if truncation:
            self.required_columns = self.required_columns + TRUNCATION_COLS
        self.requested_columns = self.required_columns
        if self.additional_columns:
            check_column_overwrite(additional_columns, self.required_columns
                                   + OPTIONAL_INPUT_COLS.get(self.fps.function_name, []))
            self.requested_columns = self.required_columns + self.get_extra_columns_from_extension()
        if kwargs:
            self.address = kwargs.get('address', None)
            self.port = kwargs.get('port', None)

    def get_extra_columns_from_extension(self):
        """Translate extra-column mappings into parser column names.

        Returns:
            list[str]: Mapping keys for Avro, or the single input field from each
            mapping for non-nested formats. Support for reading Avro files is
            intended solely for internal use; the Archive does not distribute
            files in this format.

        Raises:
            ValueError: A non-nested mapping contains an unsupported field list.
        """
        if self.file_extension in covariance_extensions:
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
        """Parse the file and apply the shared output-column casts.

        Returns:
            tuple[pandas.DataFrame, str]: Parsed data and its underlying extension.

        Notes:
            File access, format and column errors are raised by the selected parser.
        """
        parser_arguments = {
            'requested_columns': self.requested_columns,
            'optional_columns': OPTIONAL_INPUT_COLS.get(self.fps.function_name, []),
            'additional_columns': self.additional_columns,
            'selector': self.selector
        }
        if hasattr(self, 'address') and hasattr(self, 'port'):
            parser_arguments['address'] = self.address
            parser_arguments['port'] = self.port
        data, extension = self.fps.parser(**parser_arguments).parse_file(self.file, disable_info=self.disable_info)
        return cast_output(data), extension


class FileParserSelector:
    """Look up the parser factory associated with a GaiaXPy operation."""

    def __init__(self, function):
        """Store the function name, mandatory columns and parser factory.

        Args:
            function (str or callable): Operation that will consume the input.

        Raises:
            KeyError: No parser factory is registered for the operation.
        """
        self.function_name = get_function_name(function)
        self.mandatory_columns = MANDATORY_INPUT_COLS.get(self.function_name, list())
        self.parser = function_parser_dict[self.function_name]
