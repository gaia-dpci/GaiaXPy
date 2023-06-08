import unittest
from os.path import join

import pandas as pd

from gaiaxpy import extremafinder, fastfinder, linefinder
from tests.files.paths import files_path, with_missing_bp_csv_file
from tests.utils.utils import missing_bp_source_id, get_converters

import pandas.testing as pdt

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

solution_folder = 'linefinder_files'
found_fast_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_output.csv'),
                              converters=get_converters(['extrema_bp', 'extrema_rp']))
found_fast_trunc_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_trunc_output.csv'),
                                    converters=get_converters(['extrema_bp', 'extrema_rp']))
found_fast_no_bp_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_no_bp_output.csv'),
                                    converters=get_converters(['extrema_bp', 'extrema_rp']))

# Input file with xp continuous spectra
continuous_path = join(files_path, 'xp_continuous')
input_file = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')

found_fast = fastfinder(input_file, save_file=False)
found_fast_trunc = fastfinder(input_file, truncation=True, save_file=False)
found_fast_no_bp = fastfinder(with_missing_bp_csv_file, save_file=False)

isolated_missing_bp_solution_fast = found_fast_no_bp_real[found_fast_no_bp_real['source_id'] ==
                                                          missing_bp_source_id].reset_index(drop=True)

# Results to compare
solution_folder = 'linefinder_files'
found_lines_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_output.csv'))

found_lines_trunc_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_trunc_output.csv'))
found_lines_no_bp_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_no_bp_output.csv'))

# Results to test
found_lines = linefinder(input_file, save_file=False)
found_lines_trunc = linefinder(input_file, truncation=True, save_file=False)
found_lines_no_bp = linefinder(with_missing_bp_csv_file, save_file=False)
found_lines_redshift = linefinder(input_file, redshift=[0., 0.], save_file=False)

isolated_missing_bp_solution_line = found_lines_no_bp_real[found_lines_no_bp_real['source_id'] ==
                                                           missing_bp_source_id].reset_index(drop=True)

_rtol, _atol = 1e-7, 1e-7

class TestExtremaFinderArchive(unittest.TestCase):
    def test_query_input_with_missing_bp(self):
        source_ids = ('5853498713190525696', str(missing_bp_source_id), '5762406957886626816')
        query = f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN {source_ids}"
        with_missing_output = extremafinder(query, save_file=False)
        for source_id in source_ids:
            pdt.assert_frame_equal(with_missing_output[with_missing_output['source_id'] ==
                                                       source_id].reset_index(drop=True),
                                   found_extrema_no_bp_real[found_extrema_no_bp_real['source_id'] ==
                                                            source_id].reset_index(drop=True))

    def test_query_input_isolated_missing_bp(self):
        isolated_output = extremafinder("SELECT * FROM gaiadr3.gaia_source WHERE source_id IN"
                                        f" ({str(missing_bp_source_id)})", save_file=False)
        pdt.assert_frame_equal(isolated_output, isolated_solution)

    def test_list_input_with_missing_bp(self):
        sources = ['5853498713190525696', missing_bp_source_id, 5762406957886626816]
        with_missing_output = extremafinder(sources, save_file=False)
        pdt.assert_frame_equal(with_missing_output, found_extrema_no_bp_real)

    def test_list_input_isolated_missing_bp(self):
        sources = [missing_bp_source_id]
        missing_output = extremafinder(sources, save_file=False)
        pdt.assert_frame_equal(missing_output, isolated_solution)


class TestFastFinderArchive(unittest.TestCase):

    def test_query_input_with_missing_bp(self):
        source_ids = ('5853498713190525696', str(missing_bp_source_id), '5762406957886626816')
        query = f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN {source_ids}"
        with_missing_output = fastfinder(query, save_file=False)
        for source_id in source_ids:
            pdt.assert_frame_equal(with_missing_output[with_missing_output['source_id'] ==
                                                       source_id].reset_index(drop=True),
                                   found_fast_no_bp_real[found_fast_no_bp_real['source_id'] ==
                                                         source_id].reset_index(drop=True))

    def test_query_input_isolated_missing_bp(self):
        isolated_output = fastfinder(f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN"
                                     f" ({str(missing_bp_source_id)})", save_file=False)
        pdt.assert_frame_equal(isolated_output, isolated_missing_bp_solution_fast)

    def test_list_input_with_missing_bp(self):
        sources = ['5853498713190525696', missing_bp_source_id, 5762406957886626816]
        with_missing_output = fastfinder(sources, save_file=False)
        pdt.assert_frame_equal(with_missing_output, found_fast_no_bp_real)

    def test_list_input_isolated_missing_bp(self):
        sources = [missing_bp_source_id]
        missing_output = fastfinder(sources, save_file=False)
        pdt.assert_frame_equal(missing_output, isolated_missing_bp_solution_fast)


class TestLineFinderArchive(unittest.TestCase):

    def test_query_input_with_missing_bp(self):
        source_ids = ('5853498713190525696', str(missing_bp_source_id), '5762406957886626816')
        query = f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN {source_ids}"
        with_missing_output = linefinder(query, save_file=False)
        pdt.assert_frame_equal(with_missing_output, found_lines_no_bp_real.sort_values('source_id', ignore_index=True))

    def test_query_input_isolated_missing_bp(self):
        isolated_output = linefinder(f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN"
                                     f" ({str(missing_bp_source_id)})", save_file=False)
        pdt.assert_frame_equal(isolated_output, isolated_missing_bp_solution_line)

    def test_list_input_with_missing_bp(self):
        sources = ['5853498713190525696', missing_bp_source_id, 5762406957886626816]
        with_missing_output = linefinder(sources, save_file=False)
        pdt.assert_frame_equal(with_missing_output, found_lines_no_bp_real)

    def test_list_input_isolated_missing_bp(self):
        sources = [missing_bp_source_id]
        missing_output = linefinder(sources, save_file=False)
        pdt.assert_frame_equal(missing_output, isolated_missing_bp_solution_line)