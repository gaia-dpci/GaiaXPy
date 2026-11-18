"""
input_validator.py
====================================
Module to validate the input data columns, etc.
"""
from pathlib import Path

from gaiaxpy.core.generic_functions import _warning, standardise_extension
from gaiaxpy.core.generic_variables import VALID_EXTENSIONS


def validate_overwrite(overwrite):
    """Return a lowercase overwrite policy or reject an unsupported value."""
    allowed = ('yes', 'y', 'no', 'n', 'ask')
    if not isinstance(overwrite, str) or overwrite.lower() not in allowed:
        raise ValueError("overwrite must be 'yes', 'y', 'no', 'n' or 'ask'.")
    return overwrite.lower()


def validate_explicit_save_options(save_file, output_file, output_format):
    """Check saving options that do not depend on the input format."""
    if not isinstance(save_file, bool):
        raise ValueError("Parameter 'save_file' must contain a boolean value.")
    if not save_file:
        return
    if output_file is None:
        raise ValueError('output_file cannot be None.')
    filename = Path(str(output_file))
    extension = filename.suffix.lower().lstrip('.')
    if extension in VALID_EXTENSIONS:
        stem = str(filename.with_suffix(''))
        raise ValueError(f'output_file={str(filename)!r} includes an extension. To use this format, '
                         f'use output_file={stem!r} and output_format={extension!r}.')
    if output_format is None:
        return
    if not isinstance(output_format, str):
        raise TypeError('output_format must be a string or None.')
    if output_format and standardise_extension(output_format) not in VALID_EXTENSIONS:
        raise ValueError(f"The output format '{output_format}' is not supported. "
                         f"Supported formats: {', '.join(VALID_EXTENSIONS)}.")


def validate_save_arguments(default_output_file, given_output_file, default_output_format,
                            given_output_format, save_file):
    """
    Validate file saving input arguments.

    Args:
        default_output_file: Default output file name as shown in the function from which this function is being called.
        given_output_file: Output file name provided by the user.
        default_output_format: Default value for output format.
        given_output_format: Output format provided by the user.
        save_file: Argument passed to save_file parameter.
    """
    validate_explicit_save_options(save_file, given_output_file, given_output_format)
    # If the user input a number different to the default value, but didn't set save_file to True
    if default_output_file != given_output_file and not save_file:
        _warning("The argument 'output_file' was provided, but 'save_file' is set to False. Set 'save_file' to True to "
                 "store the output of the function.")
    if default_output_format != given_output_format and not save_file:
        _warning("The argument 'output_format' was provided, but 'save_file' is set to False. Set 'save_file' to True "
                 "to store the output of the function.")


def check_column_overwrite(additional_columns, required_columns):
    common_names = []
    for key, value in additional_columns.items():
        if key in required_columns:
            if not isinstance(additional_columns[key], list):
                raise TypeError('Argument additional_columns seems to be malformed.')
            if len(additional_columns[key]) == 1 and additional_columns[key][0] != key:
                common_names.append(key)
            elif len(additional_columns[key]) > 1:
                common_names.append(key)
        if isinstance(value, list) and len(value) == 1 and value[0] in required_columns and key != value[0]:
            common_names.append(key)
    if common_names:
        raise ValueError('One or more elements in the additional columns input will be renamed to a column'
                         ' required by GaiaXPy to compute the output. This is not permitted. The offending'
                         f' elements are: {", ".join(common_names)}.')
