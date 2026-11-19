import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy.generator.generator import generate
from gaiaxpy.photometric_system.photometric_system import PhotometricSystem
from tests.files.continuous import (dr3_mean_spectra_csv_file, dr3_mean_spectra_fits_file,
                                    dr3_mean_spectra_xml_binary_file)

_rtol, _atol = 1e-24, 1e-24


def test_generate_one_element_list():
    phot_system = PhotometricSystem.DR3_JKC_Std
    one_element_synthetic_photometry = generate(dr3_mean_spectra_csv_file, photometric_system=[phot_system],
                                                save_file=False)
    single_synthetic_photometry = generate(dr3_mean_spectra_csv_file, photometric_system=phot_system, save_file=False)
    # Rename columns
    pdt.assert_frame_equal(one_element_synthetic_photometry, single_synthetic_photometry, rtol=_rtol, atol=_atol)


def test_generate_csv_mix():
    phot_list = [PhotometricSystem.DR3_Euclid_VIS, PhotometricSystem.DR3_Gaia_2]
    # Current multi-result
    multi_synthetic_photometry = generate(dr3_mean_spectra_csv_file, photometric_system=phot_list, save_file=False)
    # Generate right multi-result from single photometries
    single_synthetic_photometry_euclid_vis = generate(dr3_mean_spectra_fits_file, photometric_system=phot_list[0],
                                                      save_file=False)
    single_synthetic_photometry_gaia_2 = generate(dr3_mean_spectra_xml_binary_file, photometric_system=phot_list[1],
                                                  save_file=False)
    # Concatenate but avoid duplicated source_id column
    concatenated_photometry = pd.concat([single_synthetic_photometry_euclid_vis,
                                         single_synthetic_photometry_gaia_2.drop(columns=['source_id'])], axis=1)
    # Rename multi-photometry columns
    pdt.assert_frame_equal(multi_synthetic_photometry, concatenated_photometry, rtol=_rtol, atol=_atol)


@pytest.mark.parametrize('phot_system', [None, []])
def test_no_system_given_is_none(phot_system):
    with pytest.raises(ValueError):
        generate(dr3_mean_spectra_csv_file, photometric_system=phot_system, save_file=False)


def test_empty_string_fails_type():
    with pytest.raises(TypeError):
        generate(dr3_mean_spectra_csv_file, photometric_system='', save_file=False)
