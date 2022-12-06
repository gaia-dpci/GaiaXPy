import unittest
from collections import Counter
from os.path import join

import pandas as pd
import pandas.testing as pdt

from gaiaxpy import generate, PhotometricSystem
from tests.files.paths import files_path

# Files to test parse
continuous_path = join(files_path, 'xp_continuous')
covariance_avro_file = join(continuous_path, 'MeanSpectrumSolutionWithCov.avro')
solution_path = join(files_path, 'generator_solution')

_ertol, _eatol = 1e-23, 1e-23
_rtol, _atol = 1e-14, 1e-14


class TestGenerator(unittest.TestCase):

    def test_generate_in_loop(self):
        avro_list = [covariance_avro_file for i in range(2)]
        phot_list = [PhotometricSystem.JKC_Std, PhotometricSystem.SDSS]
        columns = []
        for file in avro_list:
            photometry = generate(file, photometric_system=phot_list, error_correction=True, save_file=False)
            columns.append(list(photometry.columns))
        self.assertListEqual(columns[0], columns[1])

    def test_missing_band_csv(self):
        systems = [PhotometricSystem.Els_Custom_W09_S2, PhotometricSystem.Euclid_VIS,
                   PhotometricSystem.Gaia_2, PhotometricSystem.Gaia_DR3_Vega,
                   PhotometricSystem.Halpha_Custom_AB, PhotometricSystem.H_Custom,
                   PhotometricSystem.Hipparcos_Tycho, PhotometricSystem.HST_ACSWFC,
                   PhotometricSystem.HST_HUGS_Std, PhotometricSystem.HST_WFC3UVIS,
                   PhotometricSystem.HST_WFPC2, PhotometricSystem.IPHAS,
                   PhotometricSystem.JKC, PhotometricSystem.JKC_Std,
                   PhotometricSystem.JPAS, PhotometricSystem.JPLUS,
                   PhotometricSystem.JWST_NIRCAM, PhotometricSystem.PanSTARRS1,
                   PhotometricSystem.PanSTARRS1_Std, PhotometricSystem.Pristine,
                   PhotometricSystem.SDSS, PhotometricSystem.SDSS_Std,
                   PhotometricSystem.Stromgren, PhotometricSystem.Stromgren_Std, PhotometricSystem.WFIRST]
        missing_band_csv = join(continuous_path, 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.csv')
        generated_photometry = generate(missing_band_csv, photometric_system=systems, save_file=False)
        # Load solution
        solution_df = pd.read_csv(join(solution_path, 'generator_missing_band_solution.csv'),
                                  float_precision='round_trip')
        error_columns = [column for column in solution_df.columns if 'error' in column]
        other_columns = [column for column in solution_df.columns if not 'error' in column]
        pdt.assert_frame_equal(generated_photometry[error_columns], solution_df[error_columns], rtol=_ertol,
                               atol=_eatol)
        pdt.assert_frame_equal(generated_photometry[other_columns], solution_df[other_columns], rtol=_rtol, atol=_atol)

    def test_duplicate_columns(self):
        systems = [PhotometricSystem.Els_Custom_W09_S2, PhotometricSystem.Euclid_VIS,
                   PhotometricSystem.Gaia_2, PhotometricSystem.Gaia_DR3_Vega,
                   PhotometricSystem.Halpha_Custom_AB, PhotometricSystem.H_Custom,
                   PhotometricSystem.Hipparcos_Tycho, PhotometricSystem.HST_ACSWFC,
                   PhotometricSystem.HST_HUGS_Std, PhotometricSystem.HST_WFC3UVIS,
                   PhotometricSystem.HST_WFPC2, PhotometricSystem.IPHAS,
                   PhotometricSystem.JKC, PhotometricSystem.JKC_Std,
                   PhotometricSystem.JPAS, PhotometricSystem.JPLUS,
                   PhotometricSystem.JWST_NIRCAM, PhotometricSystem.PanSTARRS1,
                   PhotometricSystem.PanSTARRS1_Std, PhotometricSystem.Pristine,
                   PhotometricSystem.SDSS, PhotometricSystem.SDSS_Std, PhotometricSystem.Sky_Mapper,
                   PhotometricSystem.Stromgren, PhotometricSystem.Stromgren_Std, PhotometricSystem.WFIRST]
        missing_band_csv = join(continuous_path, 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.csv')
        generated_photometry = generate(missing_band_csv, photometric_system=systems, save_file=False)
        self.assertEqual(0, len([item for item, count in Counter(generated_photometry.columns).items() if count > 1]))

    def test_single_phot_object(self):
        system = PhotometricSystem.JKC
        photometry = generate(join(continuous_path, 'XP_CONTINUOUS_RAW.fits'), photometric_system=system,
                              save_file=False)
        self.assertIsInstance(photometry, pd.DataFrame)

    def test_single_phot_object_with_correction(self):
        system = PhotometricSystem.JKC
        photometry = generate(join(continuous_path, 'XP_CONTINUOUS_RAW.fits'), photometric_system=system,
                              error_correction=True, save_file=False)
        self.assertIsInstance(photometry, pd.DataFrame)
