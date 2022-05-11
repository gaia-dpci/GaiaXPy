import unittest
import filecmp
import numpy as np
import pandas as pd
from os.path import join
from tests.files import files_path
from gaiaxpy import calibrate, convert, generate, PhotometricSystem

mean_spectrum = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_dr3int6.csv')
# Create output folder
output_path = 'tests_output_files'
solution_path = join(files_path, 'output_solution')

# Note: AVRO cannot be tested by md5sum, it is binary.

def run_output_test(self, function, filename, output_format, sampling=None, phot_systems=None):
    """
    This class generates GaiaXPy output files. Then, it compares them with the
    output solution files using filecmp.
    """
    filecmp.clear_cache()
    if sampling is not None:
        function(mean_spectrum, sampling=sampling, output_path=output_path, output_file=filename, output_format=output_format)
    if phot_systems is not None:
        function(mean_spectrum, photometric_system=phot_systems, output_path=output_path, output_file=filename, output_format=output_format)
    elif sampling is None and phot_systems is None:
        function(mean_spectrum, output_path=output_path, output_file=filename, output_format=output_format)
    current_file = f'{filename}.{output_format}'
    self.assertTrue(filecmp.cmp(join(output_path, current_file), join(solution_path, current_file), shallow=False))
    if output_format in ['csv', '.csv', 'ecsv', '.ecsv'] and phot_systems is None:
        # A sampling file will be generated too (calibrate and convert), it needs to be tested
        current_sampling_file = f'{filename}_sampling.{output_format}'
        self.assertTrue(filecmp.cmp(join(output_path, current_sampling_file), join(solution_path, current_sampling_file), shallow=False))

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
        run_output_test(self, generate, 'photometry_multi', 'fits', phot_systems=[PhotometricSystem.Gaia_DR3_Vega, PhotometricSystem.HST_HUGS_Std])

    def test_save_output_xml_pristine(self):
        run_output_test(self, generate, 'photometry_pristine', 'xml', phot_systems=[PhotometricSystem.Pristine])
