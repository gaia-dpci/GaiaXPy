import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.file_parser.cast import _cast
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import (missing_bp_csv_file, with_missing_bp_csv_file, with_missing_bp_ecsv_file,
                               with_missing_bp_fits_file, with_missing_bp_xml_file, with_missing_bp_xml_plain_file,
                               no_correction_solution_path, correction_solution_path)
from tests.utils.utils import missing_bp_source_id

_rtol, _atol = 1e-7, 1e-7


@pytest.fixture(scope='module')
def with_missing_solution_df_no_corr():
    yield _cast(pd.read_csv(no_correction_solution_path, float_precision='round_trip'))


@pytest.fixture(scope='module')
def with_missing_solution_df_with_corr():
    yield _cast(pd.read_csv(correction_solution_path, float_precision='round_trip'))


@pytest.fixture(scope='module')
def phot_systems():
    system_names = ['Els_Custom_W09_S2', 'Euclid_VIS', 'Gaia_2', 'Gaia_DR3_Vega', 'Halpha_Custom_AB', 'H_Custom',
                    'Hipparcos_Tycho', 'HST_ACSWFC', 'HST_HUGS_Std', 'HST_WFC3UVIS', 'HST_WFPC2', 'IPHAS', 'JKC',
                    'JKC_Std', 'JPAS', 'JPLUS', 'JWST_NIRCAM', 'LSST', 'PanSTARRS1', 'PanSTARRS1_Std', 'Pristine',
                    'SDSS', 'SDSS_Std', 'Stromgren', 'Stromgren_Std', 'WFIRST']
    phot_systems = [PhotometricSystem[name] for name in system_names]
    yield phot_systems


@pytest.mark.parametrize('input_data', [with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,
                                        with_missing_bp_xml_file, with_missing_bp_xml_plain_file,
                                        pd.read_csv(with_missing_bp_csv_file)])
def test_generate_missing_bp_no_correction(input_data, phot_systems, with_missing_solution_df_no_corr):
    photometry_df = generate(input_data, photometric_system=phot_systems, save_file=False)
    pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, atol=_atol, rtol=_rtol)


@pytest.mark.parametrize('input_data', [with_missing_bp_csv_file,
                                        pd.read_csv(with_missing_bp_csv_file,
                                                    converters=dict([(column, lambda x: str_to_array(x))
                                                                     for column in ['bp_coefficients',
                                                                                    'bp_coefficient_errors',
                                                                                    'bp_coefficient_correlations',
                                                                                    'rp_coefficients',
                                                                                    'rp_coefficient_errors',
                                                                                    'rp_coefficient_correlations']]))])
def test_with_missing_bp_dataframe(input_data, phot_systems, with_missing_solution_df_no_corr):
    df, _ = InputReader(input_data, generate, False).read()
    photometry_df = generate(df, photometric_system=phot_systems, save_file=False)
    pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, atol=_atol, rtol=_rtol)


@pytest.mark.parametrize('file', [with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,
                                  with_missing_bp_xml_file, with_missing_bp_xml_plain_file])
def test_generate_missing_bp_with_correction(file, phot_systems, with_missing_solution_df_with_corr):
    photometry_df = generate(file, photometric_system=phot_systems, error_correction=True, save_file=False)
    pdt.assert_frame_equal(photometry_df, with_missing_solution_df_with_corr, atol=_atol, rtol=_rtol)


@pytest.mark.parametrize('input_data', [missing_bp_csv_file,
                                        pd.read_csv(missing_bp_csv_file),
                                        pd.read_csv(missing_bp_csv_file, converters=dict([(
                                                column, lambda x: str_to_array(x)) for column in
                                            ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations',
                                             'rp_coefficients', 'rp_coefficient_errors',
                                             'rp_coefficient_correlations']]))])
def test_missing_bp_dataframe_isolated(input_data, phot_systems, with_missing_solution_df_no_corr):
    missing_solution_df_no_corr = with_missing_solution_df_no_corr[with_missing_solution_df_no_corr['source_id']
                                                                   == missing_bp_source_id].reset_index(drop=True)
    photometry_df = generate(input_data, photometric_system=phot_systems, save_file=False)
    pdt.assert_frame_equal(photometry_df, missing_solution_df_no_corr, atol=_atol, rtol=_rtol)
