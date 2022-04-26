import unittest
import pandas as pd
from numpy import ndarray, dtype
from os import path
from gaiaxpy.file_parser import DataMismatchError, ExternalParser, InvalidExtensionError
from tests.files import files_path

# Files to test parse
mini_path = path.join(files_path, 'mini_files')
csv_file = path.join(mini_path, 'SPSS_mini.csv')
#fits_file = path.join(mini_path, 'XP_SPECTRA_RAW_mini.fits')
#xml_file = path.join(mini_path, 'XP_SPECTRA_RAW_mini.xml')
no_ext_file = path.join(files_path, 'no_extension_file')

parser = ExternalParser()
parsed_csv_file = parser._parse_csv(csv_file)
#parsed_fits_file = parser._parse_fits(fits_file)
#parsed_xml_file = parser._parse_xml(xml_file)


class TestExternalParserCSV(unittest.TestCase):

    def test_parse_no_extension(self):
        self.assertRaises(InvalidExtensionError, parser.parse, no_ext_file)

    def test_parse_returns_dataframe(self):
        self.assertIsInstance(parsed_csv_file, pd.DataFrame)

    # 'O' stands for object
    def test_column_types(self):
        self.assertEqual(list(parsed_csv_file.dtypes),
                         [dtype('int64'), dtype('O'), dtype('O'), dtype('O')])

    def test_flux_types(self):
        self.assertIsInstance(parsed_csv_file['flux'][0], ndarray)
        self.assertIsInstance(parsed_csv_file['flux_error'][0], ndarray)

'''
class TestExternalParserFITS(unittest.TestCase):

    def test_parse_returns_dataframe(self):
        self.assertIsInstance(parsed_fits_file, pd.DataFrame)

    # 'O' stands for object
    def test_column_types(self):
        self.assertEqual(list(parsed_fits_file.dtypes), [
                         'int64', 'int64', 'float64', 'float64', 'O', 'O'])

    def test_flux_types(self):
        self.assertIsInstance(parsed_fits_file['flux'][0], ndarray)
        self.assertIsInstance(parsed_fits_file['flux_error'][0], ndarray)


class TestExternalParserXML(unittest.TestCase):

    def test_parse_returns_dataframe(self):
        self.assertIsInstance(parsed_xml_file, pd.DataFrame)

    # 'O' stands for object
    def test_column_types(self):
        self.assertEqual(list(parsed_xml_file.dtypes), [
                         'int64', 'int64', 'float64', 'float64', 'O', 'O'])

    def test_flux_types(self):
        self.assertIsInstance(parsed_xml_file['flux'][0], ndarray)
        self.assertIsInstance(parsed_xml_file['flux_error'][0], ndarray)

    # TODO: Add more DF comparisons


class TestIncorrectFormat(unittest.TestCase):

    def test_parse_incorrect_format(self):
        with self.assertRaises(DataMismatchError):
            parser._parse_csv(fits_file)
        with self.assertRaises(DataMismatchError):
            parser._parse_fits(csv_file)
        with self.assertRaises(DataMismatchError):
            parser._parse_fits(xml_file)
        with self.assertRaises(DataMismatchError):
            parser._parse_xml(csv_file)
        with self.assertRaises(DataMismatchError):
            parser._parse_xml(fits_file)
'''
