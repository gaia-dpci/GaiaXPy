"""
input_validator.py
====================================
Module to validate the input data columns, etc.
"""


def validate_required_columns(content_columns, required_columns):
    """
    Validate whether all mandatory columns are present in the content_columns.

    Args:
        content_columns (list): List of columns in the content.
        required_columns (list): List of mandatory columns.

    Raises:
        ValueError: If some required columns are not present.
    """
    def __are_required_columns_present(_content_columns, _mandatory_columns):
        return all(column in _content_columns for column in _mandatory_columns)
    def __get_missing_columns(_content_columns, _required_columns):
        missing_cols = [col for col in _required_columns if col not in _content_columns]
        missing_cols_str = ', '.join(missing_cols)
        return missing_cols_str
    if not required_columns:
        return
    elif not __are_required_columns_present(content_columns, required_columns):
        raise ValueError(f'Some required columns are not present. Please check your data. '
                         f'Missing columns are: {__get_missing_columns(content_columns, required_columns)}.')