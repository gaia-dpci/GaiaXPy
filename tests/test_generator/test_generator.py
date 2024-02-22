from collections import Counter

import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.file_parser.cast import _cast
from tests.files.paths import missing_bp_csv_file, mean_spectrum_fits_file, gen_missing_band_sol_path

_ertol, _eatol = 1e-23, 1e-23
_rtol, _atol = 1e-14, 1e-14


@pytest.fixture(scope='module')
def systems_list():
    systems = [PhotometricSystem.Els_Custom_W09_S2, PhotometricSystem.Euclid_VIS, PhotometricSystem.Gaia_2,
               PhotometricSystem.Gaia_DR3_Vega, PhotometricSystem.Halpha_Custom_AB, PhotometricSystem.H_Custom,
               PhotometricSystem.Hipparcos_Tycho, PhotometricSystem.HST_ACSWFC, PhotometricSystem.HST_HUGS_Std,
               PhotometricSystem.HST_WFC3UVIS, PhotometricSystem.HST_WFPC2, PhotometricSystem.IPHAS,
               PhotometricSystem.JKC, PhotometricSystem.JKC_Std, PhotometricSystem.JPAS, PhotometricSystem.JPLUS,
               PhotometricSystem.JWST_NIRCAM, PhotometricSystem.PanSTARRS1, PhotometricSystem.PanSTARRS1_Std,
               PhotometricSystem.Pristine, PhotometricSystem.SDSS, PhotometricSystem.SDSS_Std,
               PhotometricSystem.Sky_Mapper, PhotometricSystem.Stromgren, PhotometricSystem.Stromgren_Std,
               PhotometricSystem.WFIRST]
    yield systems


def test_missing_band_csv(systems_list):
    generated_photometry = generate(missing_bp_csv_file, photometric_system=systems_list, save_file=False)
    # Load solution
    solution_df = _cast(pd.read_csv(gen_missing_band_sol_path, float_precision='round_trip'))
    error_columns = [column for column in solution_df.columns if 'error' in column]
    other_columns = [column for column in solution_df.columns if 'error' not in column]
    pdt.assert_frame_equal(generated_photometry[error_columns], solution_df[error_columns], rtol=_ertol, atol=_eatol)
    pdt.assert_frame_equal(generated_photometry[other_columns], solution_df[other_columns], rtol=_rtol, atol=_atol)


def test_duplicate_columns(systems_list):
    generated_photometry = generate(missing_bp_csv_file, photometric_system=systems_list, save_file=False)
    assert 0 == len([item for item, count in Counter(generated_photometry.columns).items() if count > 1])


def test_single_phot_object():
    photometry = generate(mean_spectrum_fits_file, photometric_system=PhotometricSystem.JKC, save_file=False)
    assert isinstance(photometry, pd.DataFrame)


def test_single_phot_object_with_correction():
    system = PhotometricSystem.JKC
    photometry = generate(mean_spectrum_fits_file, photometric_system=system, error_correction=True, save_file=False)
    assert isinstance(photometry, pd.DataFrame)
