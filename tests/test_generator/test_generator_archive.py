import unittest

import pandas as pd
import pandas.testing as pdt

from gaiaxpy import generate, PhotometricSystem
from tests.files.paths import no_correction_solution_path, correction_solution_path
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
