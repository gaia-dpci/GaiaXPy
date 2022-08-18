import unittest
import pandas as pd
import pandas.testing as pdt
from gaiaxpy import generate, apply_error_correction, PhotometricSystem
from os.path import join
from tests.files import files_path

# Files to test parse
continuous_path = join(files_path, 'xp_continuous')
correlation_csv_file = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')
corrected_errors_solution_path = join(files_path, 'error_correction_solution', 'corrected_errors_solution.csv')


class TestErrorCorrection(unittest.TestCase):

    def test_single_phot_object(self):
        phot_system = PhotometricSystem.Gaia_DR3_Vega
        synthetic_photometry = generate(
                        correlation_csv_file,
                        photometric_system=phot_system,
                        save_file=False)
        corrected_synth_phot = apply_error_correction(synthetic_photometry, save_file=False)
        pdt.assert_frame_equal(synthetic_photometry, corrected_synth_phot)

    def test_error_correction_no_vega(self):
        phot_list = [PhotometricSystem.Euclid_VIS, PhotometricSystem.HST_HUGS_Std]
        multi_synthetic_photometry = generate(
                        correlation_csv_file,
                        photometric_system=phot_list,
                        save_file=False)
        with self.assertRaises(ValueError):
            apply_error_correction(multi_synthetic_photometry, save_file=False)

    def test_error_correction(self):
        phot_list = [PhotometricSystem.Euclid_VIS, PhotometricSystem.Gaia_DR3_Vega, PhotometricSystem.HST_HUGS_Std]
        multi_synthetic_photometry = generate(
                        correlation_csv_file,
                        photometric_system=phot_list,
                        save_file=False)
        corrected_multiphotometry = apply_error_correction(multi_synthetic_photometry, save_file=False)
        # Load solution
        corrected_multiphotometry_solution = pd.read_csv(corrected_errors_solution_path, float_precision='round_trip')
        pdt.assert_frame_equal(corrected_multiphotometry, corrected_multiphotometry_solution)

    def test_error_correction_system_with_no_table(self):
        # Here the Halpha system has got no correction table
        phot_list = [PhotometricSystem.Euclid_VIS, PhotometricSystem.Gaia_DR3_Vega, PhotometricSystem.Halpha_Custom_AB]
        multi_synthetic_photometry = generate(
                        correlation_csv_file,
                        photometric_system=phot_list,
                        save_file=False)
        # Extract Halpha columns from the original photometry
        halpha_columns = [column for column in multi_synthetic_photometry.columns if column.startswith('HalphaCustomAb_')]
        corrected_multiphotometry = apply_error_correction(multi_synthetic_photometry, save_file=False)
        halpha_photometry = multi_synthetic_photometry[halpha_columns]  # The results for this system should not change
        # Load solution
        corrected_multiphotometry_solution = pd.read_csv(corrected_errors_solution_path, float_precision='round_trip')
        hst_columns = [column for column in corrected_multiphotometry_solution.columns if column.startswith('HstHugsStd_')]
        corrected_multiphotometry_solution_first_two = corrected_multiphotometry_solution.drop(columns=hst_columns)
        complete_solution = pd.concat([corrected_multiphotometry_solution_first_two, halpha_photometry], axis=1)
        pdt.assert_frame_equal(corrected_multiphotometry, complete_solution)
