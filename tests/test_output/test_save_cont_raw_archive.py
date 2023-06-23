import shutil
import tempfile
import unittest

from gaiaxpy import find_lines


class TestEmptyLineFinder(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def test_empty_lines(self):
        for ext in ['csv', 'ecsv', 'fits', 'xml']:
            find_lines([6236992043706872832], output_path=self.temp_dir, output_file='empty_lines', output_format=ext)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
