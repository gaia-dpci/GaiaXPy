import unittest
from os.path import join

import pandas as pd
import pandas.testing as pdt

from gaiaxpy.linefinder.linefinder import fastfinder
from tests.files.paths import *
from tests.utils.utils import get_converters

_rtol, _atol = 1e-7, 1e-7

dtypes = [('line_name', 'U12'), ('wavelength_nm', 'f8'), ('flux', 'f8'), ('depth', 'f8'), ('width', 'f8'),
          ('significance', 'f8'), ('sig_pwl', 'f8')]

solution_folder = 'finder_files'
found_fast_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_output.csv'),
                              converters=get_converters(['extrema_bp', 'extrema_rp']))
found_fast_trunc_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_trunc_output.csv'),
                                    converters=get_converters(['extrema_bp', 'extrema_rp']))
found_fast_nobp_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_nobp_output.csv'),
                                   converters=get_converters(['extrema_bp', 'extrema_rp']))

# Input file with xp continuous spectra
continuous_path = join(files_path, 'xp_continuous')
input_file = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')

found_fast = fastfinder(input_file)
found_fast_trunc = fastfinder(input_file, truncation=True)
found_fast_nobp = fastfinder(with_missing_bp_csv_file)

missing_bp_source_id = 5405570973190252288
isolated_missing_bp_solution = found_fast_nobp_real[found_fast_nobp_real['source_id'] ==
                                                    missing_bp_source_id].reset_index(drop=True)

class TestFastFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_fast, pd.DataFrame)
        self.assertIsInstance(found_fast_trunc, pd.DataFrame)
        self.assertIsInstance(found_fast_nobp, pd.DataFrame)
        pdt.assert_frame_equal(found_fast, found_fast_real, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(found_fast_trunc, found_fast_trunc_real, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(found_fast_nobp, found_fast_nobp_real, rtol=_rtol, atol=_atol)

    def test_file_input_with_missing_bp_source(self):
        with_missing_input_files = [with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,
                                    with_missing_bp_xml_file, with_missing_bp_xml_plain_file]
        for _input_file in with_missing_input_files:
            output = fastfinder(_input_file)
            pdt.assert_frame_equal(output, found_fast_nobp_real)

    # Missing BP source in isolation
    def test_file_input_isolated_missing_bp_source(self):
        missing_input_files = [missing_bp_csv_file, missing_bp_ecsv_file, missing_bp_fits_file, missing_bp_xml_file,
                               missing_bp_xml_plain_file]
        for _input_file in missing_input_files:
            output = fastfinder(_input_file)
            pdt.assert_frame_equal(output, isolated_missing_bp_solution)
    def test_df_input_with_missing_bp(self):
        with_missing_df = pd.read_csv(with_missing_bp_csv_file)
        with_missing_output = fastfinder(with_missing_df)
        pdt.assert_frame_equal(with_missing_output, found_fast_nobp_real)

    def test_df_input_isolated_missing_bp(self):
        isolated_df = pd.read_csv(missing_bp_csv_file)
        isolated_output = fastfinder(isolated_df)
        pdt.assert_frame_equal(isolated_output, isolated_missing_bp_solution)

    def test_query_input_with_missing_bp(self):
        query = "SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5853498713190525696', '5405570973190252288', " \
                "'5762406957886626816')"
        with_missing_output = fastfinder(query)
        pdt.assert_frame_equal(with_missing_output, found_fast_nobp_real.sort_values('source_id', ignore_index=True))

    def test_query_input_isolated_missing_bp(self):
        isolated_output = fastfinder("SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5405570973190252288')")
        pdt.assert_frame_equal(isolated_output, isolated_missing_bp_solution)

    def test_list_input_with_missing_bp(self):
        sources = ['5853498713190525696', missing_bp_source_id, 5762406957886626816]
        with_missing_output = fastfinder(sources)
        pdt.assert_frame_equal(with_missing_output, found_fast_nobp_real)

    def test_list_input_isolated_missing_bp(self):
        sources = [missing_bp_source_id]
        missing_output = fastfinder(sources)
        pdt.assert_frame_equal(missing_output, isolated_missing_bp_solution)
