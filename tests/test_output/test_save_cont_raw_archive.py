import unittest

from gaiaxpy import find_lines
from tests.files.paths import output_path


class TestEmptyLineFinder(unittest.TestCase):

    def test_empty_lines_csv(self):
        e = find_lines([6236992043706872832], output_path=output_path, output_file='empty_lines',
                       output_format='csv')

    def test_empty_lines_ecsv(self):
        e = find_lines([6236992043706872832], output_path=output_path, output_file='empty_lines',
                       output_format='ecsv')

    def test_empty_lines_fits(self):
        e = find_lines([6236992043706872832], output_path=output_path, output_file='empty_lines',
                       output_format='fits')

    def test_empty_lines_xml(self):
        e = find_lines([6236992043706872832], output_path=output_path, output_file='empty_lines',
                       output_format='xml')