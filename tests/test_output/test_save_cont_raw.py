import unittest
import numpy as np
import pandas as pd
from os.path import join
from tests.files import files_path
from gaiaxpy import calibrate, convert, generate, PhotometricSystem
from .utils import generate_current_md5sum_df

mean_spectrum = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_dr3int6.csv')
# Create output folder
output_path = 'tests_output_files'

# Load md5sums of the expected output files
md5sum_path = join(files_path, 'md5sum_output_files.csv')
solution_md5sum_df = pd.read_csv(md5sum_path, float_precision='round_trip')

# Note: AVRO cannot be tested by md5sum, it is binary.

def run_output_test(self, function, filename, output_format, sampling=None, phot_systems=None):
    """
    This class generates GaiaXPy output files. Then, it compares their md5sums
    with the ones stored in a test file.
    """
    if sampling is not None:
        function(mean_spectrum, sampling=sampling, output_path=output_path, output_file=filename, output_format=output_format)
    if phot_systems is not None:
        function(mean_spectrum, photometric_system=phot_systems, output_path=output_path, output_file=filename, output_format=output_format)
    elif sampling is None and phot_systems is None:
        function(mean_spectrum, output_path=output_path, output_file=filename, output_format=output_format)
    # Generate df with our answers
    current_md5sum_df = generate_current_md5sum_df(output_path)
    current_file = f'{filename}.{output_format}'
    current_file_md5sum = current_md5sum_df.loc[current_md5sum_df['filename'] == current_file]['hash'].iloc[0]
    # Get the expected result
    file_solution = solution_md5sum_df[solution_md5sum_df['filename'] == current_file]['hash'].iloc[0]
    self.assertEqual(file_solution, current_file_md5sum.decode('utf8'))
    if output_format in ['csv', '.csv', 'ecsv', '.ecsv'] and phot_systems is None:
        # A sampling file will be generated too (calibrate and convert), it needs to be tested
        current_sampling_file = f'{filename}_sampling.{output_format}'
        current_sampling_md5sum = current_md5sum_df.loc[current_md5sum_df['filename'] == current_sampling_file]['hash'].iloc[0]
        sampling_solution = solution_md5sum_df[solution_md5sum_df['filename'] == current_sampling_file]['hash'].iloc[0]
        self.assertEqual(sampling_solution, current_sampling_md5sum.decode('utf8'))


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
