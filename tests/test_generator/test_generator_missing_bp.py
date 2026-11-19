import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.file_parser.cast import _cast
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.continuous import (dr3_missing_bp_csv_file, dr3_with_missing_bp_csv_file,
                                    dr3_with_missing_bp_ecsv_file, dr3_with_missing_bp_fits_file,
                                    dr3_with_missing_bp_xml_binary_file, dr3_with_missing_bp_xml_plain_file,
                                    dr3_zipped_raw_files, dr3_zipped_individual_files)
from tests.files.generator import no_correction_solution_path, correction_solution_path
from tests.utils.utils import dr3_missing_bp_source_id

_rtol, _atol = 1e-7, 1e-7


@pytest.fixture(scope='module')
def with_missing_solution_df_no_corr():
    yield _cast(pd.read_csv(no_correction_solution_path, **CSV_FLOAT_PRECISION_KWARGS))


@pytest.fixture(scope='module')
def with_missing_solution_df_with_corr():
    yield _cast(pd.read_csv(correction_solution_path, **CSV_FLOAT_PRECISION_KWARGS))


@pytest.fixture(scope='module')
def phot_systems():
    system_names = ['DR3_Els_Custom_W09_S2', 'DR3_Euclid_VIS', 'DR3_Gaia_2', 'DR3_Gaia_Vega', 'DR3_Halpha_Custom_AB',
                    'DR3_H_Custom', 'DR3_Hipparcos_Tycho', 'DR3_HST_ACSWFC', 'DR3_HST_HUGS_Std', 'DR3_HST_WFC3UVIS',
                    'DR3_HST_WFPC2', 'DR3_IPHAS', 'DR3_JKC', 'DR3_JKC_Std', 'DR3_JPAS', 'DR3_JPLUS', 'DR3_JWST_NIRCAM',
                    'DR3_LSST', 'DR3_PanSTARRS1', 'DR3_PanSTARRS1_Std', 'DR3_Pristine', 'DR3_SDSS', 'DR3_SDSS_Std',
                    'DR3_Stromgren', 'DR3_Stromgren_Std', 'DR3_WFIRST']
    phot_systems = [PhotometricSystem[name] for name in system_names]
    yield phot_systems


@pytest.mark.parametrize('input_data',
                         [dr3_with_missing_bp_csv_file, dr3_with_missing_bp_ecsv_file, dr3_with_missing_bp_fits_file,
                          dr3_with_missing_bp_xml_binary_file, dr3_with_missing_bp_xml_plain_file,
                          pd.read_csv(dr3_with_missing_bp_csv_file, **CSV_FLOAT_PRECISION_KWARGS)] +
                         dr3_zipped_raw_files + dr3_zipped_individual_files)
def test_generate_missing_bp_no_correction(input_data, phot_systems, with_missing_solution_df_no_corr):
    photometry_df = generate(input_data, photometric_system=phot_systems, save_file=False)
    pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, atol=_atol, rtol=_rtol)


@pytest.mark.parametrize('input_data', [dr3_with_missing_bp_csv_file,
                                        pd.read_csv(dr3_with_missing_bp_csv_file,
                                                    converters=dict([(column, lambda x: str_to_array(x))
                                                                     for column in ['bp_coefficients',
                                                                                    'bp_coefficient_errors',
                                                                                    'bp_coefficient_correlations',
                                                                                    'rp_coefficients',
                                                                                    'rp_coefficient_errors',
                                                                                    'rp_coefficient_correlations']]),
                                                    **CSV_FLOAT_PRECISION_KWARGS)])
def test_with_missing_bp_dataframe(input_data, phot_systems, with_missing_solution_df_no_corr):
    df, _, _ = InputReader(input_data, generate, truncation=False).read()
    photometry_df = generate(df, photometric_system=phot_systems, save_file=False)
    pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, atol=_atol, rtol=_rtol)


@pytest.mark.parametrize('file',
                         [dr3_with_missing_bp_csv_file, dr3_with_missing_bp_ecsv_file, dr3_with_missing_bp_fits_file,
                          dr3_with_missing_bp_xml_binary_file, dr3_with_missing_bp_xml_plain_file])
def test_generate_missing_bp_with_correction(file, phot_systems, with_missing_solution_df_with_corr):
    photometry_df = generate(file, photometric_system=phot_systems, error_correction=True, save_file=False)
    pdt.assert_frame_equal(photometry_df, with_missing_solution_df_with_corr, atol=_atol, rtol=_rtol)


@pytest.mark.parametrize('input_data', [dr3_missing_bp_csv_file,
                                        pd.read_csv(dr3_missing_bp_csv_file, **CSV_FLOAT_PRECISION_KWARGS),
                                        pd.read_csv(dr3_missing_bp_csv_file, converters=dict([(
                                                column, lambda x: str_to_array(x)) for column in
                                            ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations',
                                             'rp_coefficients', 'rp_coefficient_errors',
                                             'rp_coefficient_correlations']]), **CSV_FLOAT_PRECISION_KWARGS)])
def test_missing_bp_dataframe_isolated(input_data, phot_systems, with_missing_solution_df_no_corr):
    missing_solution_df_no_corr = with_missing_solution_df_no_corr[with_missing_solution_df_no_corr['source_id']
                                                                   == dr3_missing_bp_source_id].reset_index(drop=True)
    photometry_df = generate(input_data, photometric_system=phot_systems, save_file=False)
    pdt.assert_frame_equal(photometry_df, missing_solution_df_no_corr, atol=_atol, rtol=_rtol)
