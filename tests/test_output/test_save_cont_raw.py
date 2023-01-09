import unittest
from os.path import join

import numpy as np
import pandas.testing as pdt

from gaiaxpy import calibrate, convert, generate, PhotometricSystem
from gaiaxpy.file_parser.parse_generic import GenericParser
from tests.files.paths import files_path

_rtol, _atol = 1e-10, 1e-10

mean_spectrum = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW.csv')
# Create output folder
output_path = 'tests_output_files'
solution_path = join(files_path, 'output_solution')


def compare_frames(file1, file2, extension, function_name):
    parser = GenericParser()
    if function_name in ['calibrate', 'convert']:
        array_columns = ['flux', 'flux_error']
    else:
        array_columns = None
    if extension in ['csv', 'ecsv']:
        function = parser._parse_csv
    elif extension == 'fits':
        function = parser._parse_fits
    elif extension == 'xml':
        function = parser._parse_xml
    if array_columns:
        file1 = function(file1, array_columns=array_columns)
        file2 = function(file2, array_columns=array_columns)
    else:
        file1 = function(file1)
        file2 = function(file2)
    pdt.assert_frame_equal(file1, file2, rtol=_rtol, atol=_atol)


def run_output_test(self, function, filename, output_format, sampling=None, phot_systems=None):
    """
    This class generates GaiaXPy output files. Then, it compares them with the output solution files using filecmp.
    """
    if sampling is not None:
        function(mean_spectrum, sampling=sampling, output_path=output_path, output_file=filename,
                 output_format=output_format)
    if phot_systems is not None:
        function(mean_spectrum, photometric_system=phot_systems, output_path=output_path, output_file=filename,
                 output_format=output_format)
    elif sampling is None and phot_systems is None:
        function(mean_spectrum, output_path=output_path, output_file=filename, output_format=output_format)
    current_file = f'{filename}.{output_format}'
    compare_frames(join(output_path, current_file), join(solution_path, current_file), extension=output_format,
                   function_name=function.__name__)
    if output_format in ['csv', '.csv', 'ecsv', '.ecsv'] and phot_systems is None:
        # A sampling file will be generated too (calibrate and convert), it needs to be tested
        current_sampling_file = f'{filename}_sampling.{output_format}'
        compare_frames(join(output_path, current_sampling_file), join(solution_path, current_sampling_file),
                       extension=output_format, function_name=function.__name__)


class TestSaveContRawCalibrator(unittest.TestCase):

    def test_save_output_csv(self):
        run_output_test(self, calibrate, 'calibrator', 'csv')

    def test_save_output_ecsv(self):
        run_output_test(self, calibrate, 'calibrator', 'ecsv')

    def test_save_output_fits(self):
        run_output_test(self, calibrate, 'calibrator', 'fits')

    def test_save_output_xml(self):
        run_output_test(self, calibrate, 'calibrator', 'xml')


class TestSaveContRawConverter(unittest.TestCase):

    def test_save_output_csv(self):
        run_output_test(self, convert, 'converter', 'csv')

    def test_save_output_csv_custom_0_40_350(self):
        run_output_test(self, convert, 'converter_custom_0_40_350', 'csv', sampling=np.linspace(0, 40, 350))

    def test_save_output_ecsv(self):
        run_output_test(self, convert, 'converter', 'ecsv')

    def test_save_output_fits(self):
        run_output_test(self, convert, 'converter', 'fits')

    def test_save_output_fits_custom_0_45_400(self):
        run_output_test(self, convert, 'converter_custom_0_45_400', 'fits')

    def test_save_output_xml(self):
        run_output_test(self, convert, 'converter', 'xml')

    def test_save_output_xml_custom_0_30_300(self):
        run_output_test(self, convert, 'converter_custom_0_30_300', 'xml')


class TestSaveContRawGenerator(unittest.TestCase):

    def test_save_output_csv_gaia_2(self):
        run_output_test(self, generate, 'photometry_gaia_2', 'csv', phot_systems=PhotometricSystem.Gaia_2)

    def test_save_output_ecsv_sdss_std(self):
        run_output_test(self, generate, 'photometry_sdss_std', 'ecsv', phot_systems=PhotometricSystem.SDSS_Std)

    def test_save_output_fits_multi(self):
        run_output_test(self, generate, 'photometry_multi', 'fits',
                        phot_systems=[PhotometricSystem.Gaia_DR3_Vega, PhotometricSystem.HST_HUGS_Std])

    def test_save_output_xml_pristine(self):
        run_output_test(self, generate, 'photometry_pristine', 'xml', phot_systems=[PhotometricSystem.Pristine])
