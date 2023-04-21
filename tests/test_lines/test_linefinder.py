import unittest
from configparser import ConfigParser

from gaiaxpy.lines import linefinder, extremafinder, fastfinder
from tests.files.paths import files_path

import pandas.testing as pdt
import pandas as pd


# Input file with xp continuous spectra
continuous_path = join(files_path, 'xp_continuous')
input_file = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')
# Input file with xp continuous spectra (with missing BP)
input_file_nobp = join(continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.csv')

# Results to compare
solution_folder = 'lines_solution'
found_lines_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_output.csv')
found_lines_trunc_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_trunc_output.csv')
found_extrema_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_output.csv')
found_extrema_trunc_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_trunc_output.csv')
found_fast_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_output.csv')
found_fast_trunc_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_trunc_output.csv')
found_lines_nobp_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_nobp_output.csv')
found_extrema_nobp_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_nobp_output.csv')
found_fast_nobp_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_nobp_output.csv')

# Results to test
found_lines = linefinder(input_file)
found_lines_trunc = linefinder(input_file, truncation=True)
found_extrema = extremafinder(input_file)
found_extrema_trunc = extremafinder(input_file, truncation=True)
found_fast = fastfinder(input_file)
found_fast_trunc = fastfinder(input_file, truncation=True)
found_lines_nobp = linefinder(input_file_nobp)
found_extrema_nobp = extremafinder(input_file_nobp)
found_fast_nobp = fastfinder(input_file_nobp)
found_lines_redshift = linefinder(input_file, redshift=[0.,0.])

_rtol, _atol = 1e-11, 1e-11


class TestLineFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_lines, pd.DataFrame)
        self.assertIsInstance(found_lines_trunc, pd.DataFrame)
        self.assertIsInstance(found_lines_nobp, pd.DataFrame)
        pdt.assert_frame_equal(found_lines, found_lines_real, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(found_lines_trunc, found_lines_trunc_real, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(found_lines_nobp, found_lines_nobp_real, rtol=_rtol, atol=_atol)
        
    def test_qso(self):
        pdt.assert_frame_equal(found_lines_redshift, found_lines_real, rtol=_rtol, atol=_atol)

class TestExtremaFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_extrema, pd.DataFrame)
        self.assertIsInstance(found_extrema_trunc, pd.DataFrame)
        self.assertIsInstance(found_extrema_nobp, pd.DataFrame)
        pdt.assert_frame_equal(found_extrema, found_extrema_real, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(found_extrema_trunc, found_extrema_trunc_real, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(found_extrema_nobp, found_extrema_nobp_real, rtol=_rtol, atol=_atol)

class TestFastFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_fast, pd.DataFrame)
        self.assertIsInstance(found_fast_trunc, pd.DataFrame)
        self.assertIsInstance(found_fast_nobp, pd.DataFrame)
        pdt.assert_frame_equal(found_fast, found_fast_real, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(found_fast_trunc, found_fast_trunc_real, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(found_fast_nobp, found_fast_nobp_real, rtol=_rtol, atol=_atol)

