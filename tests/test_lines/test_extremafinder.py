import unittest
from os.path import join

import pandas as pd

from gaiaxpy.lines.linefinder import extremafinder
from tests.files.paths import files_path
from tests.utils.utils import custom_void_array_comparison, get_converters

_rtol, _atol = 1e-7, 1e-7

dtypes = [('line_name', 'U12'), ('wavelength_nm', 'f8'), ('flux', 'f8'), ('depth', 'f8'), ('width', 'f8'),
          ('significance', 'f8'), ('sig_pwl', 'f8')]

# Input file with xp continuous spectra
continuous_path = join(files_path, 'xp_continuous')
input_file = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')

# Input file with xp continuous spectra (with missing BP)
input_file_nobp = join(continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.csv')

solution_folder = 'lines_files'
found_extrema_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_output.csv'),
                                 converters=get_converters('extrema', dtypes))
found_extrema_trunc_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_trunc_output.csv'),
                                       converters=get_converters('extrema', dtypes))
found_extrema_nobp_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_nobp_output.csv'),
                                      converters=get_converters('extrema', dtypes))

found_extrema = extremafinder(input_file)
found_extrema_trunc = extremafinder(input_file, truncation=True)
found_extrema_nobp = extremafinder(input_file_nobp)


class TestExtremaFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_extrema, pd.DataFrame)
        self.assertIsInstance(found_extrema_trunc, pd.DataFrame)
        self.assertIsInstance(found_extrema_nobp, pd.DataFrame)
        custom_void_array_comparison(found_extrema, found_extrema_real, 'extrema', dtypes)
        custom_void_array_comparison(found_extrema_trunc, found_extrema_trunc_real, 'extrema', dtypes)
        custom_void_array_comparison(found_extrema_nobp, found_extrema_nobp_real, 'extrema', dtypes)
