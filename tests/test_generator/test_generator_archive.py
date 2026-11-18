import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.file_parser.cast import _cast
from tests.files.generator import no_correction_solution_path, correction_solution_path
from tests.utils.utils import dr3_missing_bp_source_id as missing_bp_src

_rtol, _atol = 1e-7, 1e-7


@pytest.fixture(scope='module')
def no_corr_sol():
    yield _cast(pd.read_csv(no_correction_solution_path))


@pytest.fixture(scope='module')
def with_corr_sol():
    yield _cast(pd.read_csv(correction_solution_path))


@pytest.fixture
def systems_list():
    phot_systems = [PhotometricSystem.DR3_Els_Custom_W09_S2, PhotometricSystem.DR3_Euclid_VIS,
                    PhotometricSystem.DR3_Gaia_2, PhotometricSystem.DR3_Gaia_Vega,
                    PhotometricSystem.DR3_Halpha_Custom_AB, PhotometricSystem.DR3_H_Custom,
                    PhotometricSystem.DR3_Hipparcos_Tycho, PhotometricSystem.DR3_HST_ACSWFC,
                    PhotometricSystem.DR3_HST_HUGS_Std, PhotometricSystem.DR3_HST_WFC3UVIS,
                    PhotometricSystem.DR3_HST_WFPC2, PhotometricSystem.DR3_IPHAS, PhotometricSystem.DR3_JKC,
                    PhotometricSystem.DR3_JKC_Std, PhotometricSystem.DR3_JPAS, PhotometricSystem.DR3_JPLUS,
                    PhotometricSystem.DR3_JWST_NIRCAM, PhotometricSystem.DR3_LSST, PhotometricSystem.DR3_PanSTARRS1,
                    PhotometricSystem.DR3_PanSTARRS1_Std, PhotometricSystem.DR3_Pristine, PhotometricSystem.DR3_SDSS,
                    PhotometricSystem.DR3_SDSS_Std, PhotometricSystem.DR3_Stromgren,
                    PhotometricSystem.DR3_Stromgren_Std,
                    PhotometricSystem.DR3_WFIRST]
    yield phot_systems


@pytest.mark.archive
@pytest.mark.parametrize('input_data', [['5853498713190525696', str(missing_bp_src), '5762406957886626816'],
                                        f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ("
                                        f"'5853498713190525696', {missing_bp_src}, '5762406957886626816')"])
def test_missing_src_multiple_no_corr(input_data, systems_list, no_corr_sol):
    output_df = generate(input_data, photometric_system=systems_list, save_file=False, release=RELEASES.dr3)
    sorted_output_df = output_df.sort_values('source_id', ignore_index=True)
    sorted_solution_df = no_corr_sol.sort_values('source_id', ignore_index=True)
    pdt.assert_frame_equal(sorted_output_df, sorted_solution_df, atol=_atol, rtol=_rtol)


@pytest.mark.archive
@pytest.mark.parametrize('input_data', [['5853498713190525696', str(missing_bp_src), '5762406957886626816'],
                                        f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ("
                                        f"'5853498713190525696', {missing_bp_src}, '5762406957886626816')"])
def test_missing_src_multiple_with_corr(input_data, systems_list, with_corr_sol):
    output_df = generate(input_data, photometric_system=systems_list, save_file=False, error_correction=True,
                         release=RELEASES.dr3)
    sorted_output_df = output_df.sort_values('source_id', ignore_index=True)
    sorted_solution_df = with_corr_sol.sort_values('source_id', ignore_index=True)
    pdt.assert_frame_equal(sorted_output_df, sorted_solution_df, atol=_atol, rtol=_rtol)


@pytest.mark.archive
@pytest.mark.parametrize('input_data', [f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('{missing_bp_src}')",
                                        [missing_bp_src]])
def test_missing_src_isolated_no_corr(input_data, systems_list, no_corr_sol):
    missing_solution_df_no_corr = no_corr_sol[no_corr_sol['source_id'] == missing_bp_src].reset_index(drop=True)
    output_df = generate(input_data, photometric_system=systems_list, save_file=False, release=RELEASES.dr3)
    pdt.assert_frame_equal(output_df, missing_solution_df_no_corr, check_dtype=False, atol=_atol, rtol=_rtol)


@pytest.mark.archive
@pytest.mark.parametrize('input_data', [f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('{missing_bp_src}')",
                                        [missing_bp_src]])
def test_missing_src_isolated_with_corr(input_data, systems_list, with_corr_sol):
    missing_solution_df_with_corr = with_corr_sol[with_corr_sol['source_id'] == missing_bp_src].reset_index(drop=True)
    output_df = generate(input_data, photometric_system=systems_list, save_file=False, error_correction=True,
                         release=RELEASES.dr3)
    pdt.assert_frame_equal(output_df, missing_solution_df_with_corr, check_dtype=False, atol=_atol, rtol=_rtol)
