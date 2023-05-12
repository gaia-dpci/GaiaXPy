import unittest
from os.path import join

import pandas as pd
import pandas.testing as pdt

from gaiaxpy.lines.linefinder import fastfinder
from tests.files.paths import files_path
from tests.utils.utils import get_converters

_rtol, _atol = 1e-7, 1e-7

dtypes = [('line_name', 'U12'), ('wavelength_nm', 'f8'), ('flux', 'f8'), ('depth', 'f8'), ('width', 'f8'),
          ('significance', 'f8'), ('sig_pwl', 'f8')]

solution_folder = 'lines_files'
found_fast_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_output.csv'),
                              converters=get_converters(['extrema_bp', 'extrema_rp']))
found_fast_trunc_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_trunc_output.csv'),
                                    converters=get_converters(['extrema_bp', 'extrema_rp']))
found_fast_nobp_real = pd.read_csv(join(files_path, solution_folder, 'fastfinder_nobp_output.csv'),
                                   converters=get_converters(['extrema_bp', 'extrema_rp']))

# Input file with xp continuous spectra
continuous_path = join(files_path, 'xp_continuous')
input_file = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')

# Input file with xp continuous spectra (with missing BP)
input_file_nobp = join(continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.csv')

found_fast = fastfinder(input_file)
found_fast_trunc = fastfinder(input_file, truncation=True)
found_fast_nobp = fastfinder(input_file_nobp)


class TestFastFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_fast, pd.DataFrame)
        self.assertIsInstance(found_fast_trunc, pd.DataFrame)
        self.assertIsInstance(found_fast_nobp, pd.DataFrame)
        pdt.assert_frame_equal(found_fast, found_fast_real, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(found_fast_trunc, found_fast_trunc_real, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(found_fast_nobp, found_fast_nobp_real, rtol=_rtol, atol=_atol)
