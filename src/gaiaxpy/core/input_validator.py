"""
input_validator.py
====================================
Module to validate the input data columns, etc.
"""
from gaiaxpy.core.generic_functions import _warning


def validate_required_columns(content_columns, requested_columns):
    """
    Validate whether all mandatory columns are present in the content_columns.

    Args:
        content_columns (list): List of columns in the content.
        requested_columns (list): List of requested columns.

    Raises:
        ValueError: If some required columns are not present.
    """

    def __are_required_columns_present(_content_columns, _mandatory_columns):
        return all(column in _content_columns for column in _mandatory_columns)

    def __get_missing_columns(_content_columns, _required_columns):
        missing_cols = [col for col in _required_columns if col not in _content_columns]
        missing_cols_str = ', '.join(missing_cols)
        return missing_cols_str

    if not requested_columns:
        return
    elif not __are_required_columns_present(content_columns, requested_columns):
        raise ValueError(f'Some required columns are not present. Please check your data. '
                         f'Missing columns are: {__get_missing_columns(content_columns, requested_columns)}.')


def validate_save_arguments(default_output_file, given_output_file, default_output_format, given_output_format,
                            save_file):
    """
    Validate file saving input arguments.

    Args:
        default_output_file: Default output file name as shown in the function from which this function is being called.
        given_output_file: Output file name provided by the user.
        default_output_format: Default value for output format.
        given_output_format: Output format provided by the user.
        save_file: Argument passed to save_file parameter.
    """
    if save_file and not isinstance(save_file, bool):
        raise ValueError("Parameter 'save_file' must contain a boolean value.")
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
