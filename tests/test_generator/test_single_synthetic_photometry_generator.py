import unittest
from os import path

import pandas as pd

from gaiaxpy.generator.generator import generate
from gaiaxpy.generator.photometric_system import PhotometricSystem
from tests.files.paths import files_path

# Files to test parse
continuous_path = path.join(files_path, 'xp_continuous')
covariance_avro_file = path.join(continuous_path, 'MeanSpectrumSolutionWithCov.avro')
correlation_csv_file = path.join(continuous_path, 'XP_CONTINUOUS_RAW.csv')
correlation_fits_file = path.join(continuous_path, 'XP_CONTINUOUS_RAW.fits')
correlation_xml_plain_file = path.join(continuous_path, 'XP_CONTINUOUS_RAW_plain.xml')
correlation_xml_file = path.join(continuous_path, 'XP_CONTINUOUS_RAW.xml')

photometric_system_johnson = PhotometricSystem.JKC


class TestSingleSyntheticPhotometryGeneratorCSV(unittest.TestCase):

    def test_generate_johnson(self):
        photometric_system = PhotometricSystem.JKC
        label = photometric_system.get_system_label()
        synthetic_photometry = generate(
            correlation_csv_file,
            photometric_system=photometric_system,
            output_format='.csv',
            save_file=False)
        self.assertIsInstance(synthetic_photometry, pd.DataFrame)
        self.assertEqual(len(synthetic_photometry), 2)
        self.assertTrue(list(synthetic_photometry.columns) == ['source_id',
                                                               f'{label}_mag_U', f'{label}_mag_B', f'{label}_mag_V',
                                                               f'{label}_mag_R',
                                                               f'{label}_mag_I', f'{label}_flux_U', f'{label}_flux_B',
                                                               f'{label}_flux_V',
                                                               f'{label}_flux_R', f'{label}_flux_I',
                                                               f'{label}_flux_error_U',
                                                               f'{label}_flux_error_B', f'{label}_flux_error_V',
                                                               f'{label}_flux_error_R',
                                                               f'{label}_flux_error_I'])


class TestSingleSyntheticPhotometryGeneratorFITS(unittest.TestCase):

    def test_generate_johnson(self):
        photometric_system = PhotometricSystem.JKC
        label = photometric_system.get_system_label()
        synthetic_photometry = generate(
            correlation_fits_file,
            photometric_system=photometric_system,
            output_format='.csv',
            save_file=False)
        self.assertIsInstance(synthetic_photometry, pd.DataFrame)
        self.assertEqual(len(synthetic_photometry), 2)
        self.assertTrue(list(synthetic_photometry.columns) == ['source_id',
                                                               f'{label}_mag_U', f'{label}_mag_B', f'{label}_mag_V',
                                                               f'{label}_mag_R',
                                                               f'{label}_mag_I', f'{label}_flux_U', f'{label}_flux_B',
                                                               f'{label}_flux_V',
                                                               f'{label}_flux_R', f'{label}_flux_I',
                                                               f'{label}_flux_error_U', f'{label}_flux_error_B',
                                                               f'{label}_flux_error_V', f'{label}_flux_error_R',
                                                               f'{label}_flux_error_I'])


class TestSyntheticPhotometryGeneratorXML(unittest.TestCase):

    def test_generate_sdss_doi(self):
        photometric_system = PhotometricSystem.SDSS
        label = photometric_system.get_system_label()
        synthetic_photometry = generate(
            correlation_xml_file,
            photometric_system=photometric_system,
            output_format='.csv',
            save_file=False)
        self.assertIsInstance(synthetic_photometry, pd.DataFrame)
        self.assertEqual(len(synthetic_photometry), 2)
        self.assertTrue(list(synthetic_photometry.columns) == ['source_id',
                                                               f'{label}_mag_u', f'{label}_mag_g', f'{label}_mag_r',
                                                               f'{label}_mag_i',
                                                               f'{label}_mag_z', f'{label}_flux_u', f'{label}_flux_g',
                                                               f'{label}_flux_r',
                                                               f'{label}_flux_i', f'{label}_flux_z',
                                                               f'{label}_flux_error_u', f'{label}_flux_error_g',
                                                               f'{label}_flux_error_r', f'{label}_flux_error_i',
                                                               f'{label}_flux_error_z'])


class TestSyntheticPhotometryGeneratorAVRO(unittest.TestCase):

    def test_generate_sdss_type(self):
        photometric_system = PhotometricSystem.SDSS
        label = photometric_system.get_system_label()
        synthetic_photometry = generate(
            covariance_avro_file,
            photometric_system=photometric_system,
            output_format='avro',
            save_file=False)
        self.assertIsInstance(synthetic_photometry, pd.DataFrame)
        self.assertEqual(len(synthetic_photometry), 2)
        self.assertTrue(list(synthetic_photometry.columns) == ['source_id',
                                                               f'{label}_mag_u', f'{label}_mag_g', f'{label}_mag_r',
                                                               f'{label}_mag_i',
                                                               f'{label}_mag_z', f'{label}_flux_u', f'{label}_flux_g',
                                                               f'{label}_flux_r',
                                                               f'{label}_flux_i', f'{label}_flux_z',
                                                               f'{label}_flux_error_u', f'{label}_flux_error_g',
                                                               f'{label}_flux_error_r', f'{label}_flux_error_i',
                                                               f'{label}_flux_error_z'])
