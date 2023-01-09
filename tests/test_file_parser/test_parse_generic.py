import unittest
from os import path

import numpy as np

from gaiaxpy.file_parser.parse_generic import _get_file_extension, DataMismatchError, \
    GenericParser, InvalidExtensionError
from tests.files.paths import files_path

parser = GenericParser()

array = np.array([1, 2, 3, 4, 5, 6])
size = 3

mini_path = path.join(files_path, 'mini_files')
csv_file = path.join(mini_path, 'XP_SPECTRA_RAW_mini.csv')
fits_file = path.join(mini_path, 'XP_SPECTRA_RAW_mini.fits')
xml_file = path.join(mini_path, 'XP_SPECTRA_RAW_mini.xml')


class TestGetFileExtension(unittest.TestCase):

    def test_get_valid_extensions(self):
        self.assertEqual(_get_file_extension(csv_file), 'csv')
        self.assertEqual(_get_file_extension(fits_file), 'fits')
        self.assertEqual(_get_file_extension(xml_file), 'xml')

    def test_get_no_extension(self):
        self.assertEqual(_get_file_extension('path/file'), '')

    # Managing directories is not necessary because they return '' which is an
    # invalid extension
    def test_get_directory(self):
        self.assertEqual(_get_file_extension('path/file/'), '')


class TestParser(unittest.TestCase):

    def test_get_parser_error(self):
        self.assertRaises(InvalidExtensionError, parser.get_parser, '')

    def test_get_parser_extensions(self):
        self.assertEqual(parser.get_parser('csv'), parser._parse_csv)
        self.assertEqual(parser.get_parser('fits'), parser._parse_fits)
        self.assertEqual(parser.get_parser('xml'), parser._parse_xml)

    def test_parse_incorrect_format(self):
        with self.assertRaises(DataMismatchError):
            parser._parse_fits(csv_file)
        with self.assertRaises(DataMismatchError):
            parser._parse_fits(xml_file)
        with self.assertRaises(DataMismatchError):
            parser._parse_xml(csv_file)
        with self.assertRaises(DataMismatchError):
            parser._parse_xml(fits_file)
