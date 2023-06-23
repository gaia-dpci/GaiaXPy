import unittest
from os.path import join

import pandas as pd
import pandas.testing as pdt

from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import missing_bp_csv_file, with_missing_bp_csv_file, with_missing_bp_ecsv_file, \
    with_missing_bp_fits_file, with_missing_bp_xml_file, with_missing_bp_xml_plain_file, missing_bp_fits_file, \
    missing_bp_xml_file, missing_bp_ecsv_file, missing_bp_xml_plain_file, no_correction_solution_path, \
    correction_solution_path
from tests.utils.utils import missing_bp_source_id

_rtol, _atol = 1e-7, 1e-7

# Load solution
with_missing_solution_df_no_corr = pd.read_csv(no_correction_solution_path, float_precision='high')
with_missing_solution_df_with_corr = pd.read_csv(correction_solution_path, float_precision='high')

missing_solution_df_no_corr = with_missing_solution_df_no_corr[with_missing_solution_df_no_corr['source_id']
                                                               == missing_bp_source_id].reset_index(drop=True)
missing_solution_df_with_corr = with_missing_solution_df_with_corr[with_missing_solution_df_no_corr['source_id']
                                                                   == missing_bp_source_id].reset_index(drop=True)

phot_systems = [PhotometricSystem.Els_Custom_W09_S2, PhotometricSystem.Euclid_VIS, PhotometricSystem.Gaia_2,
                PhotometricSystem.Gaia_DR3_Vega, PhotometricSystem.Halpha_Custom_AB, PhotometricSystem.H_Custom,
                PhotometricSystem.Hipparcos_Tycho, PhotometricSystem.HST_ACSWFC, PhotometricSystem.HST_HUGS_Std,
                PhotometricSystem.HST_WFC3UVIS, PhotometricSystem.HST_WFPC2, PhotometricSystem.IPHAS,
                PhotometricSystem.JKC, PhotometricSystem.JKC_Std, PhotometricSystem.JPAS, PhotometricSystem.JPLUS,
                PhotometricSystem.JWST_NIRCAM, PhotometricSystem.LSST, PhotometricSystem.PanSTARRS1,
                PhotometricSystem.PanSTARRS1_Std, PhotometricSystem.Pristine, PhotometricSystem.SDSS,
                PhotometricSystem.SDSS_Std, PhotometricSystem.Stromgren, PhotometricSystem.Stromgren_Std,
                PhotometricSystem.WFIRST]


class TestGeneratorMissingBPFileInput(unittest.TestCase):

    def test_generate_missing_bp_no_correction_csv(self):
        photometry_df = generate(with_missing_bp_csv_file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_csv_isolated(self):
        photometry_df = generate(missing_bp_csv_file, photometric_system=phot_systems, error_correction=True,
                                 save_file=False)
        pdt.assert_frame_equal(photometry_df, missing_solution_df_with_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_no_correction_ecsv(self):
        photometry_df = generate(with_missing_bp_ecsv_file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_ecsv_isolated(self):
        photometry_df = generate(missing_bp_ecsv_file, photometric_system=phot_systems, error_correction=True,
                                 save_file=False)
        pdt.assert_frame_equal(photometry_df, missing_solution_df_with_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_no_correction_fits(self):
        photometry_df = generate(with_missing_bp_fits_file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_fits_isolated(self):
        photometry_df = generate(missing_bp_fits_file, photometric_system=phot_systems, error_correction=True,
                                 save_file=False)
        pdt.assert_frame_equal(photometry_df, missing_solution_df_with_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_no_correction_bin_xml(self):
        photometry_df = generate(with_missing_bp_xml_file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_bin_xml_isolated(self):
        photometry_df = generate(missing_bp_xml_file, photometric_system=phot_systems, error_correction=True,
                                 save_file=False)
        pdt.assert_frame_equal(photometry_df, missing_solution_df_with_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_no_correction_plain_xml(self):
        photometry_df = generate(with_missing_bp_xml_plain_file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_plain_xml_isolated(self):
        photometry_df = generate(missing_bp_xml_plain_file, photometric_system=phot_systems, error_correction=True,
                                 save_file=False)
        pdt.assert_frame_equal(photometry_df, missing_solution_df_with_corr, rtol=_rtol, atol=_atol)


class TestGeneratorMissingBPDataFrameInput(unittest.TestCase):

    def test_missing_bp_simple_dataframe(self):
        # Test dataframe containing strings instead of arrays
        df = pd.read_csv(with_missing_bp_csv_file)
        output_df = generate(df, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(output_df, with_missing_solution_df_no_corr, atol=_atol, rtol=_rtol)

    def test_missing_bp_simple_dataframe_isolated(self):
        # Test dataframe containing strings instead of arrays
        df = pd.read_csv(missing_bp_csv_file)
        output_df = generate(df, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df_no_corr, atol=_atol, rtol=_rtol)

    def test_missing_bp_array_dataframe(self):
        # Convert columns in the dataframe to arrays (but not to matrices)
        array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficients',
                         'rp_coefficient_errors', 'rp_coefficient_correlations']
        converters = dict([(column, lambda x: str_to_array(x)) for column in array_columns])
        df = pd.read_csv(with_missing_bp_csv_file, converters=converters)
        output_df = generate(df, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(output_df, with_missing_solution_df_no_corr, atol=_atol, rtol=_rtol)

    def test_missing_bp_array_dataframe_isolated(self):
        # Convert columns in the dataframe to arrays (but not to matrices)
        array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficients',
                         'rp_coefficient_errors', 'rp_coefficient_correlations']
        converters = dict([(column, lambda x: str_to_array(x)) for column in array_columns])
        df = pd.read_csv(missing_bp_csv_file, converters=converters)
        output_df = generate(df, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df_no_corr, atol=_atol, rtol=_rtol)

    def test_missing_bp_parsed_dataframe(self):
        # Test completely parsed (arrays + matrices) dataframe
        df, _ = InputReader(with_missing_bp_csv_file, generate).read()
        output_df = generate(df, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(output_df, with_missing_solution_df_no_corr, atol=_atol, rtol=_rtol)

    def test_missing_bp_parsed_dataframe_isolated(self):
        # Test completely parsed (arrays + matrices) dataframe
        df, _ = InputReader(missing_bp_csv_file, generate).read()
        output_df = generate(df, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df_no_corr, atol=_atol, rtol=_rtol)
