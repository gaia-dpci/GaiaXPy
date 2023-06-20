import unittest
from os.path import join

import pandas as pd
import pandas.testing as pdt

from gaiaxpy import find_extrema, find_fast, find_lines
from tests.files.paths import files_path, with_missing_bp_csv_file, mean_spectrum_csv_file
from tests.utils.utils import missing_bp_source_id, get_converters

solution_folder = 'linefinder_files'
found_extrema_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_output.csv'))
found_extrema_trunc_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_trunc_output.csv'))
found_extrema_no_bp_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_no_bp_output.csv'))

found_extrema = find_extrema(mean_spectrum_csv_file, save_file=False)
found_extrema_trunc = find_extrema(mean_spectrum_csv_file, truncation=True, save_file=False)
found_extrema_no_bp = find_extrema(with_missing_bp_csv_file, save_file=False)

isolated_solution = found_extrema_no_bp_real[found_extrema_no_bp_real['source_id'] ==
                                             missing_bp_source_id].reset_index(drop=True)

solution_folder = 'linefinder_files'
found_fast_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_output.csv'),
                              converters=get_converters(['extrema_bp', 'extrema_rp']))
found_fast_trunc_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_trunc_output.csv'),
                                    converters=get_converters(['extrema_bp', 'extrema_rp']))
found_fast_no_bp_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_no_bp_output.csv'),
                                    converters=get_converters(['extrema_bp', 'extrema_rp']))

found_fast = find_fast(mean_spectrum_csv_file, save_file=False)
found_fast_trunc = find_fast(mean_spectrum_csv_file, truncation=True, save_file=False)
found_fast_no_bp = find_fast(with_missing_bp_csv_file, save_file=False)

isolated_missing_bp_solution_fast = found_fast_no_bp_real[found_fast_no_bp_real['source_id'] ==
                                                          missing_bp_source_id].reset_index(drop=True)

# Results to compare
solution_folder = 'linefinder_files'
found_lines_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_output.csv'))

found_lines_trunc_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_trunc_output.csv'))
found_lines_no_bp_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_no_bp_output.csv'))

# Results to test
found_lines = find_lines(mean_spectrum_csv_file, save_file=False)
found_lines_trunc = find_lines(mean_spectrum_csv_file, truncation=True, save_file=False)
found_lines_no_bp = find_lines(with_missing_bp_csv_file, save_file=False)
found_lines_redshift = find_lines(mean_spectrum_csv_file, redshift=[0., 0.], save_file=False)

isolated_missing_bp_solution_line = found_lines_no_bp_real[found_lines_no_bp_real['source_id'] ==
                                                           missing_bp_source_id].reset_index(drop=True)

_rtol, _atol = 1e-7, 1e-7


class TestExtremaFinderArchive(unittest.TestCase):
    def test_query_input_with_missing_bp(self):
        source_ids = ('5853498713190525696', str(missing_bp_source_id), '5762406957886626816')
        query = f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN {source_ids}"
        with_missing_output = find_extrema(query, save_file=False)
        for source_id in source_ids:
            pdt.assert_frame_equal(with_missing_output[with_missing_output['source_id'] ==
                                                       source_id].reset_index(drop=True),
                                   found_extrema_no_bp_real[found_extrema_no_bp_real['source_id'] ==
                                                            source_id].reset_index(drop=True))

    def test_query_input_isolated_missing_bp(self):
        isolated_output = find_extrema("SELECT * FROM gaiadr3.gaia_source WHERE source_id IN"
                                       f" ({str(missing_bp_source_id)})", save_file=False)
        pdt.assert_frame_equal(isolated_output, isolated_solution)

    def test_list_input_with_missing_bp(self):
        sources = ['5853498713190525696', missing_bp_source_id, 5762406957886626816]
        with_missing_output = find_extrema(sources, save_file=False)
        pdt.assert_frame_equal(with_missing_output, found_extrema_no_bp_real)

    def test_list_input_isolated_missing_bp(self):
        sources = [missing_bp_source_id]
        missing_output = find_extrema(sources, save_file=False)
        pdt.assert_frame_equal(missing_output, isolated_solution)


class TestFastFinderArchive(unittest.TestCase):

    def test_query_input_with_missing_bp(self):
        source_ids = ('5853498713190525696', str(missing_bp_source_id), '5762406957886626816')
        query = f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN {source_ids}"
        with_missing_output = find_fast(query, save_file=False)
        for source_id in source_ids:
            pdt.assert_frame_equal(with_missing_output[with_missing_output['source_id'] ==
                                                       source_id].reset_index(drop=True),
                                   found_fast_no_bp_real[found_fast_no_bp_real['source_id'] ==
                                                         source_id].reset_index(drop=True))

    def test_query_input_isolated_missing_bp(self):
        isolated_output = find_fast(f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN"
                                    f" ({str(missing_bp_source_id)})", save_file=False)
        pdt.assert_frame_equal(isolated_output, isolated_missing_bp_solution_fast)

    def test_list_input_with_missing_bp(self):
        sources = ['5853498713190525696', missing_bp_source_id, 5762406957886626816]
        with_missing_output = find_fast(sources, save_file=False)
        pdt.assert_frame_equal(with_missing_output, found_fast_no_bp_real)

    def test_list_input_isolated_missing_bp(self):
        sources = [missing_bp_source_id]
        missing_output = find_fast(sources, save_file=False)
        pdt.assert_frame_equal(missing_output, isolated_missing_bp_solution_fast)


class TestLineFinderArchive(unittest.TestCase):

    def test_query_input_with_missing_bp(self):
        source_ids = ('5853498713190525696', str(missing_bp_source_id), '5762406957886626816')
        query = f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN {source_ids}"
        with_missing_output = find_lines(query, save_file=False)
        with_missing_output = with_missing_output.sort_values(by=['source_id', 'line_name'], ignore_index=True)
        found_lines_no_bp_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_no_bp_output.csv'))
        found_lines_no_bp_real = found_lines_no_bp_real.sort_values(by=['source_id', 'line_name'], ignore_index=True)
        pdt.assert_frame_equal(with_missing_output, found_lines_no_bp_real)

    def test_query_input_isolated_missing_bp(self):
        isolated_output = find_lines(f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN"
                                     f" ({str(missing_bp_source_id)})", save_file=False)
        pdt.assert_frame_equal(isolated_output, isolated_missing_bp_solution_line)

    def test_list_input_with_missing_bp(self):
        sources = ['5853498713190525696', missing_bp_source_id, 5762406957886626816]
        with_missing_output = find_lines(sources, save_file=False)
        pdt.assert_frame_equal(with_missing_output, found_lines_no_bp_real)

    def test_list_input_isolated_missing_bp(self):
        sources = [missing_bp_source_id]
        missing_output = find_lines(sources, save_file=False)
        pdt.assert_frame_equal(missing_output, isolated_missing_bp_solution_line)
