import unittest

from gaiaxpy.core.generic_functions import format_additional_columns


class TestFormatAdditionalColumns(unittest.TestCase):

    def test_none_type(self):
        self.assertEqual(format_additional_columns(None), dict())

    def test_str_type(self):
        col = 'test_col'
        self.assertEqual(format_additional_columns(col), {col: [col]})
