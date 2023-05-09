import unittest
from os.path import join

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import linefinder, extremafinder, fastfinder
from gaiaxpy.core.generic_functions import str_to_array
# from gaiaxpy.core.generic_functions import str_to_array
from tests.files.paths import files_path

# Input file with xp continuous spectra
continuous_path = join(files_path, 'xp_continuous')
input_file = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')
# Input file with xp continuous spectra (with missing BP)
input_file_nobp = join(continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.csv')

lines_dtypes = [('line_name', 'U12'), ('wavelength_nm', 'f8'), ('flux', 'f8'), ('depth', 'f8'), ('width', 'f8'),
                ('significance', 'f8'), ('sig_pwl', 'f8')]

extrema_dtypes = [('line_name', '<U12'), ('wavelength_nm', '<f8'), ('flux', '<f8'), ('depth', '<f8'), ('width', '<f8'),
                  ('significance', '<f8'), ('sig_pwl', '<f8')]

dtypes_dict = {'lines': lines_dtypes, 'extrema': extrema_dtypes}

_rtol, _atol = 1e-7, 1e-7


def custom_comparison(df1, df2, column):
    dtypes = dtypes_dict[column]
    df1_lines = df1[column].values
    df2_lines = df2[column].values
    if len(df1_lines) == len(df2_lines):
        for lines1, lines2 in zip(df1_lines, df2_lines):
            if len(lines1) == len(lines2):
                for line1, line2 in zip(lines1, lines2):
                    # Convert line to dictionary
                    d1 = {key: line1[key] for key, _ in dtypes}
                    d2 = {key: line2[key] for key, _ in dtypes}
                    line_name1 = d1.pop('line_name')
                    line_name2 = d2.pop('line_name')
                    assert line_name1 == line_name2
                    assert d1 == pytest.approx(d2, rel=_rtol, abs=_atol, nan_ok=True)
        return
    raise ValueError('DataFrames are different.')


# Define the converter function
def str_to_array_rec(input_str, dtypes):
    lst = eval(input_str)
    lst = [tuple(element) for element in lst]
    output = [np.array(line, dtype=dtypes) for line in lst]
    return np.array(output)


def get_converters(columns):
    if len(columns) == 1:
        column = columns[0]
        dtypes = dtypes_dict[column]
        return {column: lambda x: str_to_array_rec(x, dtypes)}
    elif len(columns) > 1:
        return {column: lambda x: str_to_array(x) for column in columns}


# Results to compare
solution_folder = 'lines_files'
found_lines_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_output.csv'),
                               converters=get_converters('lines'))
found_lines_trunc_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_trunc_output.csv'),
                                     converters=get_converters('lines'))
found_lines_nobp_real = pd.read_csv(join(files_path, solution_folder, 'linefinder_nobp_output.csv'),
                                    converters=get_converters('lines'))

found_extrema_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_output.csv'),
                                 converters=get_converters('extrema'))
found_extrema_trunc_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_trunc_output.csv'),
                                       converters=get_converters('extrema'))
found_extrema_nobp_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_nobp_output.csv'),
                                      converters=get_converters('extrema'))

found_fast_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_output.csv'),
                              converters=get_converters(['extrema_bp', 'extrema_rp']))
found_fast_trunc_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_trunc_output.csv'),
                                    converters=get_converters(['extrema_bp', 'extrema_rp']))
found_fast_nobp_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_nobp_output.csv'),
                                   converters=get_converters(['extrema_bp', 'extrema_rp']))

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
found_lines_redshift = linefinder(input_file, redshift=[0., 0.])


class TestLineFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_lines, pd.DataFrame)
        self.assertIsInstance(found_lines_trunc, pd.DataFrame)
        self.assertIsInstance(found_lines_nobp, pd.DataFrame)
        custom_comparison(found_lines, found_lines_real, 'lines')
        custom_comparison(found_lines_trunc, found_lines_trunc_real, 'lines')
        custom_comparison(found_lines_nobp, found_lines_nobp_real, 'lines')

    def test_qso(self):
        custom_comparison(found_lines_redshift, found_lines_real, 'lines')


class TestExtremaFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_extrema, pd.DataFrame)
        self.assertIsInstance(found_extrema_trunc, pd.DataFrame)
        self.assertIsInstance(found_extrema_nobp, pd.DataFrame)
        custom_comparison(found_extrema, found_extrema_real, 'extrema')
        custom_comparison(found_extrema_trunc, found_extrema_trunc_real, 'extrema')
        custom_comparison(found_extrema_nobp, found_extrema_nobp_real, 'extrema')


class TestFastFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_fast, pd.DataFrame)
        self.assertIsInstance(found_fast_trunc, pd.DataFrame)
        self.assertIsInstance(found_fast_nobp, pd.DataFrame)
        pdt.assert_frame_equal(found_fast, found_fast_real, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(found_fast_trunc, found_fast_trunc_real, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(found_fast_nobp, found_fast_nobp_real, rtol=_rtol, atol=_atol)
