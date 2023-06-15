import unittest

import pandas as pd
import pandas.testing as pdt

from gaiaxpy import find_lines
from tests.files.paths import *
from tests.utils.utils import missing_bp_source_id

# Input file with xp continuous spectra
continuous_path = join(files_path, 'xp_continuous')
input_file = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')

_rtol, _atol = 1e-7, 1e-7


# Results to compare
solution_folder = 'linefinder_files'
found_lines_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_output.csv'))

found_lines_trunc_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_trunc_output.csv'))
found_lines_no_bp_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_no_bp_output.csv'))

# Results to test
found_lines = find_lines(input_file, save_file=False)
found_lines_trunc = find_lines(input_file, truncation=True, save_file=False)
found_lines_no_bp = find_lines(with_missing_bp_csv_file, save_file=False)
found_lines_redshift = find_lines(input_file, redshift=[0., 0.], save_file=False)

isolated_missing_bp_solution = found_lines_no_bp_real[found_lines_no_bp_real['source_id'] ==
                                                      missing_bp_source_id].reset_index(drop=True)


class TestLineFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_lines, pd.DataFrame)
        self.assertIsInstance(found_lines_trunc, pd.DataFrame)
        self.assertIsInstance(found_lines_no_bp, pd.DataFrame)
        pdt.assert_frame_equal(found_lines, found_lines_real)
        pdt.assert_frame_equal(found_lines_trunc, found_lines_trunc_real)
        pdt.assert_frame_equal(found_lines_no_bp, found_lines_no_bp_real)

    def test_qso(self):
        pdt.assert_frame_equal(found_lines_redshift, found_lines_real)


class TestLineFinderInput(unittest.TestCase):

    # With missing BP source
    def test_file_input_with_missing_bp_source(self):
        with_missing_input_files = [with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,
                                    with_missing_bp_xml_file, with_missing_bp_xml_plain_file]
        for _input_file in with_missing_input_files:
            output = find_lines(_input_file, save_file=False)
            pdt.assert_frame_equal(output, found_lines_no_bp_real)

    # Missing BP source in isolation
    def test_file_input_isolated_missing_bp_source(self):
        isolated_solution = found_lines_no_bp_real[found_lines_no_bp_real['source_id'] ==
                                                   missing_bp_source_id].reset_index(drop=True)
        missing_input_files = [missing_bp_csv_file, missing_bp_ecsv_file, missing_bp_fits_file, missing_bp_xml_file,
                               missing_bp_xml_plain_file]
        for _input_file in missing_input_files:
            output = find_lines(_input_file, save_file=False)
            pdt.assert_frame_equal(output, isolated_solution)

    def test_df_input_with_missing_bp(self):
        with_missing_df = pd.read_csv(with_missing_bp_csv_file)
        with_missing_output = find_lines(with_missing_df, save_file=False)
        pdt.assert_frame_equal(with_missing_output, found_lines_no_bp_real)

    def test_df_input_isolated_missing_bp(self):
        isolated_df = pd.read_csv(missing_bp_csv_file)
        isolated_output = find_lines(isolated_df, save_file=False)
        pdt.assert_frame_equal(isolated_output, isolated_missing_bp_solution)
