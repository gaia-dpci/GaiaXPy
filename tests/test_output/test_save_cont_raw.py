import shutil
import tempfile
import unittest
from os.path import join

import numpy as np
import pandas as pd
import pandas.testing as pdt
from astropy.io.votable import parse_single_table
from astropy.table import Table

from gaiaxpy import calibrate, convert, generate, PhotometricSystem
from gaiaxpy.file_parser.parse_generic import GenericParser
from tests.files.paths import output_sol_path, mean_spectrum_csv_file

_rtol, _atol = 1e-10, 1e-10


def _parse_output_fits(fits_file, _array_columns=None):
    table = Table.read(fits_file, format='fits')
    columns = table.columns.keys()
    fits_as_gen = ([table[column][index] for column in columns] for index, _ in enumerate(table))
    return pd.DataFrame(fits_as_gen, columns=columns)


def _parse_output_xml(xml_file, _array_columns=None):
    votable = parse_single_table(xml_file).to_table(use_names_over_ids=True)
    if _array_columns:
        columns = list(votable.columns)
        votable_as_list = ([votable[column][index].filled() if column in _array_columns else votable[column][index]
                            for column in columns] for index, _ in enumerate(votable))
        df = pd.DataFrame(votable_as_list, columns=columns)
    else:
        df = votable.to_pandas()
    return df


def compare_frames(output_file, solution_file, extension, function_name):
    parser = GenericParser()
    function, array_columns = None, None
    if function_name in ['calibrate', 'convert']:
        array_columns = ['flux', 'flux_error']
    if extension in ['csv', 'ecsv']:
        function = parser._parse_csv
    elif extension == 'fits':
        function = _parse_output_fits
    elif extension == 'xml':
        function = _parse_output_xml
    if array_columns:
        output_df = function(output_file, _array_columns=array_columns)
        solution_df = function(solution_file, _array_columns=array_columns)
    else:
        output_df = function(output_file)
        solution_df = function(solution_file)
    pdt.assert_frame_equal(output_df, solution_df, rtol=_rtol, atol=_atol)


class TestSaveContRaw(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def run_output_test(self, function, filename, output_format, sampling=None, phot_systems=None):
        """
        This class generates GaiaXPy output files. Then, it compares them with the output solution files using filecmp.
        """
        output_path = self.temp_dir
        if sampling is not None:
            function(mean_spectrum_csv_file, sampling=sampling, output_path=output_path, output_file=filename,
                     output_format=output_format)
        if phot_systems is not None:
            function(mean_spectrum_csv_file, photometric_system=phot_systems, output_path=output_path,
                     output_file=filename,
                     output_format=output_format)
        elif sampling is None and phot_systems is None:
            function(mean_spectrum_csv_file, output_path=output_path, output_file=filename, output_format=output_format)
        current_file = f'{filename}.{output_format}'
        compare_frames(join(output_path, current_file), join(output_sol_path, current_file), extension=output_format,
                       function_name=function.__name__)
        if output_format in ['csv', '.csv'] and phot_systems is None and 'find' not in function.__name__:
            # A sampling file will be generated too (calibrate and convert), it needs to be tested
            current_sampling_file = f'{filename}_sampling.{output_format}'
            compare_frames(join(output_path, current_sampling_file), join(output_sol_path, current_sampling_file),
                           extension=output_format, function_name=function.__name__)

    def test_save_output_calibrator(self):
        for extension in ['csv', 'ecsv', 'fits', 'xml']:
            self.run_output_test(calibrate, 'calibrator', extension)

    def test_save_output_converter(self):
        for extension in ['csv', 'ecsv', 'fits', 'xml']:
            self.run_output_test(convert, 'converter', extension)

    def test_save_output_csv_custom_0_40_350(self):
        self.run_output_test(convert, 'converter_custom_0_40_350', 'csv', sampling=np.linspace(0, 40, 350))

    def test_save_output_fits_custom_0_45_400(self):
        self.run_output_test(convert, 'converter_custom_0_45_400', 'fits')

    def test_save_output_xml_custom_0_30_300(self):
        self.run_output_test(convert, 'converter_custom_0_30_300', 'xml')

    def test_save_output_csv_gaia_2(self):
        self.run_output_test(generate, 'photometry_gaia_2', 'csv', phot_systems=PhotometricSystem.Gaia_2)

    def test_save_output_ecsv_sdss_std(self):
        self.run_output_test(generate, 'photometry_sdss_std', 'ecsv', phot_systems=PhotometricSystem.SDSS_Std)

    def test_save_output_fits_multi(self):
        self.run_output_test(generate, 'photometry_multi', 'fits', phot_systems=[PhotometricSystem.Gaia_DR3_Vega,
                                                                            PhotometricSystem.HST_HUGS_Std])

    def test_save_output_xml_pristine(self):
        self.run_output_test(generate, 'photometry_pristine', 'xml', phot_systems=[PhotometricSystem.Pristine])
