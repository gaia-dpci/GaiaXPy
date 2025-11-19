import re
import sys
from collections import Counter
from io import StringIO

import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import generate, remove_additional_systems, load_additional_systems
from gaiaxpy.file_parser.cast import _cast
from tests.files.paths import missing_bp_csv_file, mean_spectrum_fits_file, gen_missing_band_sol_path
from tests.test_generator.generator_paths import additional_filters_dir

_rtol, _atol = 1e-23, 1e-23


@pytest.fixture(scope='function')
def __ps():
    PhotometricSystem = remove_additional_systems()
    yield PhotometricSystem


@pytest.fixture
def systems_list(__ps):
    systems = [__ps.Els_Custom_W09_S2, __ps.Euclid_VIS, __ps.Gaia_2, __ps.Gaia_DR3_Vega, __ps.Halpha_Custom_AB,
               __ps.H_Custom, __ps.Hipparcos_Tycho, __ps.HST_ACSWFC, __ps.HST_HUGS_Std, __ps.HST_WFC3UVIS,
               __ps.HST_WFPC2, __ps.IPHAS, __ps.JKC, __ps.JKC_Std, __ps.JPAS, __ps.JPLUS, __ps.JWST_NIRCAM,
               __ps.PanSTARRS1, __ps.PanSTARRS1_Std, __ps.Pristine, __ps.SDSS, __ps.SDSS_Std, __ps.Sky_Mapper,
               __ps.Stromgren, __ps.Stromgren_Std, __ps.WFIRST]
    yield systems


def test_missing_band_csv(systems_list):
    generated_photometry = generate(missing_bp_csv_file, photometric_system=systems_list, save_file=False)
    solution_df = _cast(pd.read_csv(gen_missing_band_sol_path, float_precision='round_trip'))
    pdt.assert_frame_equal(generated_photometry, solution_df, rtol=_rtol, atol=_atol)


def test_duplicate_columns(systems_list):
    generated_photometry = generate(missing_bp_csv_file, photometric_system=systems_list, save_file=False)
    assert 0 == len([item for item, count in Counter(generated_photometry.columns).items() if count > 1])


def test_single_phot_object(__ps):
    photometry = generate(mean_spectrum_fits_file, photometric_system=__ps.JKC, save_file=False)
    assert isinstance(photometry, pd.DataFrame)


def test_single_phot_object_with_correction(__ps):
    system = __ps.JKC
    photometry = generate(mean_spectrum_fits_file, photometric_system=system, error_correction=True, save_file=False)
    assert isinstance(photometry, pd.DataFrame)


def test_error_correction_additional_systems(__ps):
    __ps = load_additional_systems(additional_filters_dir)
    additional_systems = [system for system in __ps if system.get_system_name().startswith('USER_')]

    captured_output = StringIO()
    sys.stderr = captured_output
    _ = generate(mean_spectrum_fits_file, photometric_system=additional_systems, error_correction=True, save_file=False)
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
