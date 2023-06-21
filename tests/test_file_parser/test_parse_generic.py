import unittest

import numpy as np

from gaiaxpy.file_parser.parse_generic import _get_file_extension, GenericParser, InvalidExtensionError
from tests.files.paths import mini_csv_file, mini_fits_file, mini_xml_file

parser = GenericParser()

array = np.array([1, 2, 3, 4, 5, 6])
size = 3


class TestGetFileExtension(unittest.TestCase):

    def test_get_valid_extensions(self):
        self.assertEqual(_get_file_extension(mini_csv_file), 'csv')
        self.assertEqual(_get_file_extension(mini_fits_file), 'fits')
        self.assertEqual(_get_file_extension(mini_xml_file), 'xml')

    def test_get_no_extension(self):
        self.assertEqual(_get_file_extension('path/file'), '')

    # Managing directories is not necessary because they return '' which is an invalid extension
    def test_get_directory(self):
        self.assertEqual(_get_file_extension('path/file/'), '')


class TestParser(unittest.TestCase):

    def test_get_parser_error(self):
        self.assertRaises(InvalidExtensionError, parser.get_parser, '')

    def test_get_parser_extensions(self):
        self.assertEqual(parser.get_parser('csv'), parser._parse_csv)
        self.assertEqual(parser.get_parser('fits'), parser._parse_fits)
        self.assertEqual(parser.get_parser('xml'), parser._parse_xml)
