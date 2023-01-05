import unittest
from os.path import join

import pandas as pd
import pandas.testing as pdt

from gaiaxpy import generate, PhotometricSystem
from tests.files.paths import files_path

_rtol, _atol = 1e-7, 1e-7

# Load solution
no_correction_solution_path = join(files_path, 'generator_solution', 'generator_solution_with_missing_BP.csv')
correction_solution_path = join(files_path, 'generator_solution',
                                'generator_solution_with_missing_BP_error_correction.csv')
solution_df_no_corr = pd.read_csv(no_correction_solution_path, float_precision='round_trip')
solution_df_with_corr = pd.read_csv(correction_solution_path, float_precision='round_trip')

phot_systems = [PhotometricSystem.Els_Custom_W09_S2, PhotometricSystem.Euclid_VIS, PhotometricSystem.Gaia_2,
                PhotometricSystem.Gaia_DR3_Vega, PhotometricSystem.Halpha_Custom_AB, PhotometricSystem.H_Custom,
                PhotometricSystem.Hipparcos_Tycho, PhotometricSystem.HST_ACSWFC, PhotometricSystem.HST_HUGS_Std,
                PhotometricSystem.HST_WFC3UVIS, PhotometricSystem.HST_WFPC2, PhotometricSystem.IPHAS,
                PhotometricSystem.JKC, PhotometricSystem.JKC_Std, PhotometricSystem.JPAS, PhotometricSystem.JPLUS,
                PhotometricSystem.JWST_NIRCAM, PhotometricSystem.LSST, PhotometricSystem.PanSTARRS1,
                PhotometricSystem.PanSTARRS1_Std, PhotometricSystem.Pristine, PhotometricSystem.SDSS,
                PhotometricSystem.SDSS_Std, PhotometricSystem.Stromgren, PhotometricSystem.Stromgren_Std,
                PhotometricSystem.WFIRST]


class TestGeneratorMissingBP(unittest.TestCase):

    def test_generate_missing_bp_no_correction_csv(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
        photometry_df = generate(file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_csv(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
        photometry_df = generate(file, photometric_system=phot_systems, error_correction=True, save_file=False)
        pdt.assert_frame_equal(photometry_df, solution_df_with_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_no_correction_ecsv(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.ecsv')
        photometry_df = generate(file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_ecsv(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.ecsv')
        photometry_df = generate(file, photometric_system=phot_systems, error_correction=True, save_file=False)
        pdt.assert_frame_equal(photometry_df, solution_df_with_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_no_correction_fits(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.fits')
        photometry_df = generate(file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_fits(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.fits')
        photometry_df = generate(file, photometric_system=phot_systems, error_correction=True, save_file=False)
        pdt.assert_frame_equal(photometry_df, solution_df_with_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_no_correction_bin_xml(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.xml')
        photometry_df = generate(file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_bin_xml(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.xml')
        photometry_df = generate(file, photometric_system=phot_systems, error_correction=True, save_file=False)
        pdt.assert_frame_equal(photometry_df, solution_df_with_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_no_correction_plain_xml(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP_plain.xml')
        photometry_df = generate(file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_plain_xml(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP_plain.xml')
        photometry_df = generate(file, photometric_system=phot_systems, error_correction=True, save_file=False)
        pdt.assert_frame_equal(photometry_df, solution_df_with_corr, rtol=_rtol, atol=_atol)
