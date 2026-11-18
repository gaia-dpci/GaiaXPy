import re
import sys
from collections import Counter
from io import StringIO

import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import generate, remove_additional_systems, load_additional_systems, PhotometricSystem
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.file_parser.cast import _cast
from tests.files.continuous import dr3_missing_bp_csv_file, dr3_mean_spectra_fits_file
from tests.files.generator import additional_filters_dir
from tests.files.generator import gen_missing_band_sol_path

_rtol, _atol = 1e-23, 1e-23


@pytest.fixture(autouse=True)
def remove_systems():
    yield
    remove_additional_systems()


@pytest.fixture(scope='function')
def __ps():
    yield PhotometricSystem


@pytest.fixture
def systems_list(__ps):
    systems = [__ps.DR3_Els_Custom_W09_S2, __ps.DR3_Euclid_VIS, __ps.DR3_Gaia_2, __ps.DR3_Gaia_Vega,
               __ps.DR3_Halpha_Custom_AB, __ps.DR3_H_Custom, __ps.DR3_Hipparcos_Tycho, __ps.DR3_HST_ACSWFC,
               __ps.DR3_HST_HUGS_Std, __ps.DR3_HST_WFC3UVIS, __ps.DR3_HST_WFPC2, __ps.DR3_IPHAS, __ps.DR3_JKC,
               __ps.DR3_JKC_Std, __ps.DR3_JPAS, __ps.DR3_JPLUS, __ps.DR3_JWST_NIRCAM, __ps.DR3_PanSTARRS1,
               __ps.DR3_PanSTARRS1_Std, __ps.DR3_Pristine, __ps.DR3_SDSS, __ps.DR3_SDSS_Std, __ps.DR3_Sky_Mapper,
               __ps.DR3_Stromgren, __ps.DR3_Stromgren_Std, __ps.DR3_WFIRST]
    yield systems


def test_missing_band_csv(systems_list):
    generated_photometry = generate(dr3_missing_bp_csv_file, photometric_system=systems_list, save_file=False)
    solution_df = _cast(pd.read_csv(gen_missing_band_sol_path, **CSV_FLOAT_PRECISION_KWARGS))
    pdt.assert_frame_equal(generated_photometry, solution_df, rtol=_rtol, atol=_atol)


def test_duplicate_columns(systems_list):
    generated_photometry = generate(dr3_missing_bp_csv_file, photometric_system=systems_list, save_file=False)
    assert 0 == len([item for item, count in Counter(generated_photometry.columns).items() if count > 1])


def test_single_phot_object(__ps):
    photometry = generate(dr3_mean_spectra_fits_file, photometric_system=__ps.DR3_JKC, save_file=False)
    assert isinstance(photometry, pd.DataFrame)


def test_single_phot_object_with_correction(__ps):
    system = __ps.DR3_JKC
    photometry = generate(dr3_mean_spectra_fits_file, photometric_system=system, error_correction=True, save_file=False)
    assert isinstance(photometry, pd.DataFrame)


def test_error_correction_additional_systems(__ps):
    __ps = load_additional_systems(additional_filters_dir)
    additional_systems = [system for system in __ps if system.get_system_name().startswith('USER_DR3')]
    captured_output = StringIO()
    sys.stderr = captured_output
    _ = generate(dr3_mean_spectra_fits_file, photometric_system=additional_systems, error_correction=True,
                 save_file=False)
    sys.stderr = sys.__stderr__
    # Get the printed output
    printed_text = captured_output.getvalue().strip().split('\n')
    # Check if the expected output is in the captured output
    _pattern = (r'UserWarning: System \w+ does not have a correction table\. The program will not apply error '
                r'correction over this system.')
    matches = [re.match(_pattern, text) for text in printed_text]
    # Check that match always occurs at the beginning
    assert sum(m.start() for m in matches) == 0
    # Check that length matches the expected length
    matches_lens = (m.end() - m.start() for m in matches)
    ptext_lens = (len(p) for p in printed_text)
    assert list(matches_lens) == list(ptext_lens)
