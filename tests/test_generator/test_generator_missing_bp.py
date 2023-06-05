import unittest
from os.path import join

import pandas as pd
import pandas.testing as pdt

from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import *
from tests.utils.utils import missing_bp_source_id

_rtol, _atol = 1e-7, 1e-7

# Load solution
no_correction_solution_path = join(files_path, 'generator_solution', 'generator_solution_with_missing_BP.csv')
correction_solution_path = join(files_path, 'generator_solution',
                                'generator_solution_with_missing_BP_error_correction.csv')
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
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
        photometry_df = generate(file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_csv_isolated(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.csv')
        photometry_df = generate(file, photometric_system=phot_systems, error_correction=True, save_file=False)
        pdt.assert_frame_equal(photometry_df, missing_solution_df_with_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_no_correction_ecsv(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.ecsv')
        photometry_df = generate(file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_ecsv_isolated(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.ecsv')
        photometry_df = generate(file, photometric_system=phot_systems, error_correction=True, save_file=False)
        pdt.assert_frame_equal(photometry_df, missing_solution_df_with_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_no_correction_fits(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.fits')
        photometry_df = generate(file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_fits_isolated(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.fits')
        photometry_df = generate(file, photometric_system=phot_systems, error_correction=True, save_file=False)
        pdt.assert_frame_equal(photometry_df, missing_solution_df_with_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_no_correction_bin_xml(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.xml')
        photometry_df = generate(file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_bin_xml_isolated(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.xml')
        photometry_df = generate(file, photometric_system=phot_systems, error_correction=True, save_file=False)
        pdt.assert_frame_equal(photometry_df, missing_solution_df_with_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_no_correction_plain_xml(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP_plain.xml')
        photometry_df = generate(file, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(photometry_df, with_missing_solution_df_no_corr, rtol=_rtol, atol=_atol)

    def test_generate_missing_bp_with_correction_plain_xml_isolated(self):
        file = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_missing_BP_plain_dr3int6.xml')
        photometry_df = generate(file, photometric_system=phot_systems, error_correction=True, save_file=False)
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


class TestGeneratorMissingBPQueryInput(unittest.TestCase):

    def test_missing_bp_query(self):
        query = f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5853498713190525696', " \
                f"{missing_bp_source_id}, '5762406957886626816')"
        output_df = generate(query, photometric_system=phot_systems, save_file=False)
        sorted_output_df = output_df.sort_values('source_id', ignore_index=True)
        sorted_solution_df = with_missing_solution_df_no_corr.sort_values('source_id', ignore_index=True)
        pdt.assert_frame_equal(sorted_output_df, sorted_solution_df, atol=_atol, rtol=_rtol)

    def test_missing_bp_query_isolated(self):
        query = f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ({missing_bp_source_id})"
        output_df = generate(query, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df_no_corr, atol=_atol, rtol=_rtol)


class TestGeneratorMissingBPListInput(unittest.TestCase):

    def test_missing_bp_list(self):
        src_list = ['5853498713190525696', str(missing_bp_source_id), '5762406957886626816']
        output_df = generate(src_list, photometric_system=phot_systems, save_file=False)
        sorted_output_df = output_df.sort_values('source_id', ignore_index=True)
        sorted_solution_df = with_missing_solution_df_no_corr.sort_values('source_id', ignore_index=True)
        pdt.assert_frame_equal(sorted_output_df, sorted_solution_df, check_dtype=False, atol=_atol, rtol=_rtol)

    def test_missing_bp_isolated(self):
        src_list = [missing_bp_source_id]
        output_df = generate(src_list, photometric_system=phot_systems, save_file=False)
        pdt.assert_frame_equal(output_df, missing_solution_df_no_corr, check_dtype=False, atol=_atol, rtol=_rtol)

