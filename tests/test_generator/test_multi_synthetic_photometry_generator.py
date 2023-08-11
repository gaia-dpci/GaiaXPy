import unittest

import pandas as pd
import pandas.testing as pdt

from gaiaxpy.generator.generator import generate
from gaiaxpy.generator.photometric_system import PhotometricSystem
from tests.files.paths import mean_spectrum_csv_file, mean_spectrum_fits_file, mean_spectrum_xml_file

_rtol, _atol = 1e-24, 1e-24


class TestMultiSyntheticPhotometryGenerator(unittest.TestCase):

    def test_generate_empty_list(self):
        with self.assertRaises(ValueError):
            generate(mean_spectrum_csv_file, photometric_system=[], save_file=False)

    def test_generate_one_element_list(self):
        phot_system = PhotometricSystem.JKC_Std
        one_element_synthetic_photometry = generate(mean_spectrum_csv_file, photometric_system=[phot_system],
                                                    save_file=False)
        single_synthetic_photometry = generate(mean_spectrum_csv_file, photometric_system=phot_system, save_file=False)
        # Rename columns
        pdt.assert_frame_equal(one_element_synthetic_photometry, single_synthetic_photometry, rtol=_rtol, atol=_atol)

    def test_generate_csv_mix(self):
        phot_list = [PhotometricSystem.Euclid_VIS, PhotometricSystem.Gaia_2]
        # Current multi-result
        multi_synthetic_photometry = generate(mean_spectrum_csv_file, photometric_system=phot_list, save_file=False)
        # Generate right multi-result from single photometries
        single_synthetic_photometry_euclid_vis = generate(mean_spectrum_fits_file, photometric_system=phot_list[0],
                                                          save_file=False)
        single_synthetic_photometry_gaia_2 = generate(mean_spectrum_xml_file, photometric_system=phot_list[1],
                                                      save_file=False)
        # Concatenate but avoid duplicated source_id column
        concatenated_photometry = pd.concat([single_synthetic_photometry_euclid_vis,
                                             single_synthetic_photometry_gaia_2.drop(columns=['source_id'])], axis=1)
        # Rename multi-photometry columns
        pdt.assert_frame_equal(multi_synthetic_photometry, concatenated_photometry, rtol=_rtol, atol=_atol)

    def test_no_system_given_is_none(self):
        with self.assertRaises(ValueError):
            generate(mean_spectrum_csv_file, photometric_system=None)
        with self.assertRaises(ValueError):
            generate(mean_spectrum_csv_file, photometric_system=[])
        with self.assertRaises(ValueError):
            generate(mean_spectrum_csv_file, photometric_system='')
