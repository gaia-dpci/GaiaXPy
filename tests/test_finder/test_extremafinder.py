import unittest

import pandas as pd

from gaiaxpy.finder.linefinder import extremafinder
from tests.files.paths import *
from tests.utils.utils import custom_void_array_comparison, get_converters

missing_bp_source_id = 5405570973190252288
_rtol, _atol = 1e-7, 1e-7

dtypes = [('line_name', 'U12'), ('wavelength_nm', 'f8'), ('flux', 'f8'), ('depth', 'f8'), ('width', 'f8'),
          ('significance', 'f8'), ('sig_pwl', 'f8')]

# Input file with xp continuous spectra
continuous_path = join(files_path, 'xp_continuous')
input_file = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')

solution_folder = 'finder_files'
found_extrema_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_output.csv'),
                                 converters=get_converters('extrema', dtypes))
found_extrema_trunc_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_trunc_output.csv'),
                                       converters=get_converters('extrema', dtypes))
found_extrema_nobp_real = pd.read_csv(join(files_path, solution_folder, 'extremafinder_nobp_output.csv'),
                                      converters=get_converters('extrema', dtypes))

found_extrema = extremafinder(input_file)
found_extrema_trunc = extremafinder(input_file, truncation=True)
found_extrema_nobp = extremafinder(with_missing_bp_csv_file)


class TestExtremaFinder(unittest.TestCase):

    def test_output(self):
        self.assertIsInstance(found_extrema, pd.DataFrame)
        self.assertIsInstance(found_extrema_trunc, pd.DataFrame)
        self.assertIsInstance(found_extrema_nobp, pd.DataFrame)
        custom_void_array_comparison(found_extrema, found_extrema_real, 'extrema', dtypes)
        custom_void_array_comparison(found_extrema_trunc, found_extrema_trunc_real, 'extrema', dtypes)
        custom_void_array_comparison(found_extrema_nobp, found_extrema_nobp_real, 'extrema', dtypes)

    # With missing BP source
    def test_file_input_with_missing_bp_source(self):
        with_missing_input_files = [with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,
                                    with_missing_bp_xml_file, with_missing_bp_xml_plain_file]
        for _input_file in with_missing_input_files:
            output = extremafinder(_input_file)
            custom_void_array_comparison(output, found_extrema_nobp_real, 'extrema', dtypes)

    # Missing BP source in isolation
    def test_file_input_isolated_missing_bp_source(self):
        isolated_solution = found_extrema_nobp_real[found_extrema_nobp_real['source_id'] ==
                                                    missing_bp_source_id].reset_index(drop=True)
        missing_input_files = [missing_bp_csv_file, missing_bp_ecsv_file, missing_bp_fits_file, missing_bp_xml_file,
                               missing_bp_xml_plain_file]
        for _input_file in missing_input_files:
            output = extremafinder(_input_file)
            custom_void_array_comparison(output, isolated_solution, 'extrema', dtypes)
