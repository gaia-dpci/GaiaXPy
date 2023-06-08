import unittest

import pandas as pd

import pandas.testing as pdt

from gaiaxpy.linefinder.linefinder import extremafinder
from tests.files.paths import *
from tests.utils.utils import missing_bp_source_id

_rtol, _atol = 1e-7, 1e-7

# Input file with xp continuous spectra
continuous_path = join(files_path, 'xp_continuous')
input_file = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')

solution_folder = 'linefinder_files'
found_extrema_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_output.csv'))
found_extrema_trunc_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_trunc_output.csv'))
found_extrema_no_bp_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_no_bp_output.csv'))

found_extrema = extremafinder(input_file, save_file=False)
found_extrema_trunc = extremafinder(input_file, truncation=True, save_file=False)
found_extrema_no_bp = extremafinder(with_missing_bp_csv_file, save_file=False)

isolated_solution = found_extrema_no_bp_real[found_extrema_no_bp_real['source_id'] ==
                                             missing_bp_source_id].reset_index(drop=True)


class TestExtremaFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_extrema, pd.DataFrame)
        self.assertIsInstance(found_extrema_trunc, pd.DataFrame)
        self.assertIsInstance(found_extrema_no_bp, pd.DataFrame)
        pdt.assert_frame_equal(found_extrema, found_extrema_real)
        pdt.assert_frame_equal(found_extrema_trunc, found_extrema_trunc_real)
        pdt.assert_frame_equal(found_extrema_no_bp, found_extrema_no_bp_real)

    # With missing BP source
    def test_file_input_with_missing_bp_source(self):
        with_missing_input_files = [with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,
                                    with_missing_bp_xml_file, with_missing_bp_xml_plain_file]
        for _input_file in with_missing_input_files:
            output = extremafinder(_input_file, save_file=False)
            pdt.assert_frame_equal(output, found_extrema_no_bp_real)

    # Missing BP source in isolation
    def test_file_input_isolated_missing_bp_source(self):
        missing_input_files = [missing_bp_csv_file, missing_bp_ecsv_file, missing_bp_fits_file, missing_bp_xml_file,
                               missing_bp_xml_plain_file]
        for _input_file in missing_input_files:
            output = extremafinder(_input_file, save_file=False)
            pdt.assert_frame_equal(output, isolated_solution)

    def test_df_input_with_missing_bp(self):
        with_missing_df = pd.read_csv(with_missing_bp_csv_file)
        with_missing_output = extremafinder(with_missing_df, save_file=False)
        pdt.assert_frame_equal(with_missing_output, found_extrema_no_bp_real)

    def test_df_input_isolated_missing_bp(self):
        isolated_df = pd.read_csv(missing_bp_csv_file)
        isolated_output = extremafinder(isolated_df, save_file=False)
        pdt.assert_frame_equal(isolated_output, isolated_solution)
