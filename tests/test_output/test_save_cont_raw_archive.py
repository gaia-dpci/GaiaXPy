import unittest

from gaiaxpy import linefinder


class TestEmptyLineFinder(unittest.TestCase):

    def test_empty_lines_csv(self):
        e = linefinder([6236992043706872832], output_path='tests_output_files', output_file='empty_lines',
                       output_format='csv')

    def test_empty_lines_ecsv(self):
        e = linefinder([6236992043706872832], output_path='tests_output_files', output_file='empty_lines',
                       output_format='ecsv')

    def test_empty_lines_fits(self):
        e = linefinder([6236992043706872832], output_path='tests_output_files', output_file='empty_lines',
                       output_format='fits')

    def test_empty_lines_xml(self):
        e = linefinder([6236992043706872832], output_path='tests_output_files', output_file='empty_lines',
                       output_format='xml')