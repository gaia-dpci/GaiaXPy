from gaiaxpy.core.generic_functions import format_additional_columns


def test_none_type():
    assert format_additional_columns(None) == dict()


def test_str_type():
    col = 'test_col'
    assert format_additional_columns(col) == {col: [col]}
