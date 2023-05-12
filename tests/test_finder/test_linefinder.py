import unittest

import pandas as pd

from gaiaxpy import linefinder
from tests.files.paths import *
from tests.utils.utils import custom_void_array_comparison, get_converters

# Input file with xp continuous spectra
continuous_path = join(files_path, 'xp_continuous')
input_file = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')
# Input file with xp continuous spectra (with missing BP)
input_file_nobp = join(continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.csv')

missing_bp_source_id = 5405570973190252288
_rtol, _atol = 1e-7, 1e-7

dtypes = [('line_name', 'U12'), ('wavelength_nm', 'f8'), ('flux', 'f8'), ('depth', 'f8'), ('width', 'f8'),
          ('significance', 'f8'), ('sig_pwl', 'f8')]

# Results to compare
solution_folder = 'finder_files'
found_lines_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_output.csv'),
                               converters=get_converters('lines', dtypes))

found_lines_trunc_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_trunc_output.csv'),
                                     converters=get_converters('lines', dtypes))
found_lines_nobp_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_nobp_output.csv'),
                                    converters=get_converters('lines', dtypes))

# Results to test
found_lines = linefinder(input_file)
found_lines_trunc = linefinder(input_file, truncation=True)
found_lines_nobp = linefinder(input_file_nobp)
found_lines_redshift = linefinder(input_file, redshift=[0., 0.])


class TestLineFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_lines, pd.DataFrame)
        self.assertIsInstance(found_lines_trunc, pd.DataFrame)
        self.assertIsInstance(found_lines_nobp, pd.DataFrame)
        custom_void_array_comparison(found_lines, found_lines_real, 'lines', dtypes)
        custom_void_array_comparison(found_lines_trunc, found_lines_trunc_real, 'lines', dtypes)
        custom_void_array_comparison(found_lines_nobp, found_lines_nobp_real, 'lines', dtypes)

    def test_qso(self):
        custom_void_array_comparison(found_lines_redshift, found_lines_real, 'lines', dtypes)


class TestLineFinderInput(unittest.TestCase):

    # With missing BP source
    def test_file_input_with_missing_bp_source(self):
        with_missing_input_files = [with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,
                                    with_missing_bp_xml_file, with_missing_bp_xml_plain_file]
        for _input_file in with_missing_input_files:
            output = linefinder(_input_file)
            custom_void_array_comparison(output, found_lines_nobp_real, 'lines', dtypes)

    # Missing BP source in isolation
    def test_file_input_isolated_missing_bp_source(self):
        isolated_solution = found_lines_nobp_real[found_lines_nobp_real['source_id'] ==
                                                  missing_bp_source_id].reset_index(drop=True)
        missing_input_files = [missing_bp_csv_file, missing_bp_ecsv_file, missing_bp_fits_file, missing_bp_xml_file,
                               missing_bp_xml_plain_file]
        for _input_file in missing_input_files:
            output = linefinder(_input_file)
            custom_void_array_comparison(output, isolated_solution, 'lines', dtypes)
