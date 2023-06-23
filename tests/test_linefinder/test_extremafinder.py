import unittest

import pandas as pd
import pandas.testing as pdt

from gaiaxpy.linefinder.linefinder import find_extrema
from tests.files.paths import missing_bp_csv_file, missing_bp_ecsv_file, missing_bp_fits_file, missing_bp_xml_file,\
    missing_bp_xml_plain_file, with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,\
    with_missing_bp_xml_file, with_missing_bp_xml_plain_file, mean_spectrum_csv_file
from tests.test_linefinder.linefinder_solutions import found_extrema_real, found_extrema_trunc_real
from tests.test_linefinder.test_finder_archive import found_extrema_no_bp_real
from tests.utils.utils import missing_bp_source_id

_rtol, _atol = 1e-7, 1e-7

found_extrema = find_extrema(mean_spectrum_csv_file, save_file=False)
found_extrema_trunc = find_extrema(mean_spectrum_csv_file, truncation=True, save_file=False)
found_extrema_no_bp = find_extrema(with_missing_bp_csv_file, save_file=False)

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
            output = find_extrema(_input_file, save_file=False)
            pdt.assert_frame_equal(output, found_extrema_no_bp_real)

    # Missing BP source in isolation
    def test_file_input_isolated_missing_bp_source(self):
        missing_input_files = [missing_bp_csv_file, missing_bp_ecsv_file, missing_bp_fits_file, missing_bp_xml_file,
                               missing_bp_xml_plain_file]
        for _input_file in missing_input_files:
            output = find_extrema(_input_file, save_file=False)
            pdt.assert_frame_equal(output, isolated_solution)

    def test_df_input_with_missing_bp(self):
        input_files = [with_missing_bp_csv_file, missing_bp_csv_file]
        solutions = [found_extrema_no_bp_real, isolated_solution]
        for file, sol in zip(input_files, solutions):
            df = pd.read_csv(file)
            output = find_extrema(df, save_file=False)
            pdt.assert_frame_equal(output, sol)
