import math
import unittest

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.colour_equation.xp_filter_system_colour_equation import apply_colour_equation
from gaiaxpy.core.generic_functions import cast_output
from tests.files.paths import colour_eq_csv_file
from tests.test_colour_equation.colour_equation_paths import col_eq_sol_johnson_path

_rtol, _atol = 1e-24, 1e-24


def get_mag_error(flux, flux_error):
    return 2.5 * flux_error / (flux * math.log(10))


phot_system = PhotometricSystem.SDSS_Std
label = phot_system.get_system_label()
variables = ['mag', 'flux', 'flux_error']
bands = ['u', 'g', 'r', 'i', 'z']
sdss_std_cols = ['source_id'] + [f'{label}_{v}_{b}' for v in variables for b in bands]


class TestSingleColourEquation(unittest.TestCase):

    def test_gaiaxpy_vs_pmn_photometry(self):
        """
        Compare the photometries got for a subset of sources of a particular CSV file
        for GaiaXPy and PMN's Java code. A subset of sources is used as it is not possible to extract
        the original data for all the sources in 'Landolt_Johnson_STD_v375wiv142r_SAMPLE.csv'
        (PMN's photometry) from the archive. This test compares magnitude errors.
        """
        phot_system = PhotometricSystem.JKC_Std
        bands = phot_system.get_bands()
        label = phot_system.get_system_label()
        output_photometry = generate(colour_eq_csv_file, phot_system, save_file=False)
        # Read PMN photometry
        # Source for which data could be extracted from Geapre
        sources_to_keep = [4408087461749558912, 4408087908426160384, 4408088011505376128]
        johnson_solution_df = pd.read_csv(col_eq_sol_johnson_path)
        johnson_solution_df = johnson_solution_df.loc[johnson_solution_df['source_id'].isin(sources_to_keep)]
        for source_id in sources_to_keep:
            output_source = output_photometry[output_photometry['source_id'] == source_id].iloc[0]
            for band in bands:
                # Compare mag errors
                computed_mag_error = get_mag_error(output_source[f'{label}_flux_{band}'],
                                                   output_source[f'{label}_flux_error_{band}'])
                pmn_source = johnson_solution_df[johnson_solution_df['source_id'] == source_id].iloc[0]
                npt.assert_almost_equal(computed_mag_error, pmn_source[f'{band}_err'])  # decimal=6 by default
                # Compare magnitudes
                npt.assert_almost_equal(output_source[f'{label}_mag_{band}'], pmn_source[band])

    def test_johnson_std_csv(self):
        """
        Compare the results of GaiaXPy and PMN's results for the application of the colour equation in Johnson_Std.
        """
        phot_system = PhotometricSystem.JKC_Std
        label = phot_system.get_system_label()
        # The band the changes in Johnson_Std is U, all the other stay the same
        affected_band = 'U'
        output_photometry = generate(colour_eq_csv_file, phot_system, save_file=False)
        # DataFrame with all the columns that
        unchanged_columns = [column for column in output_photometry.columns if affected_band not in column]
        affected_columns = [column for column in output_photometry.columns if affected_band in column]
        output_photometry_equal = output_photometry[unchanged_columns]
        pdt.assert_frame_equal(output_photometry_equal, output_photometry[unchanged_columns])
        # Compare changes in photometry
        output_photometry_differences = output_photometry[['source_id'] + affected_columns]
        for source_id in output_photometry['source_id'].values:
            # solution columns format: {band}, {band}_err
            johnson_solution_df = pd.read_csv(col_eq_sol_johnson_path)
            source_solution = johnson_solution_df[johnson_solution_df['source_id'] == source_id].iloc[0]
            source_result = output_photometry_differences[output_photometry_differences['source_id'] ==
                                                          source_id].iloc[0]
            # Compare mags
            npt.assert_almost_equal(source_solution[affected_band], source_result[f'{label}_mag_{affected_band}'])
            # Compare errors
            mag_error = get_mag_error(source_result[f'{label}_flux_{affected_band}'],
                                      source_result[f'{label}_flux_error_{affected_band}'])
            npt.assert_almost_equal(source_solution[f'{affected_band}_err'], mag_error)
        # Read PMN's photometry
        pmn_corrected_photometry = pd.read_csv(col_eq_sol_johnson_path)
        sources_to_keep = [4408087461749558912, 4408087908426160384, 4408088011505376128]
        pmn_corrected_photometry = pmn_corrected_photometry.loc[pmn_corrected_photometry['source_id'].isin(
            sources_to_keep)]
        # Compare U band mags
        npt.assert_array_almost_equal(pmn_corrected_photometry['U'].values,
                                      output_photometry_differences[f'{label}_mag_U'].values)
        for source_id in sources_to_keep:
            pmn_source = pmn_corrected_photometry[pmn_corrected_photometry['source_id'] == source_id].iloc[0]
            corrected_source = output_photometry[output_photometry['source_id'] == source_id].iloc[0]
            bands = phot_system.get_bands()
            for band in bands:
                pmn_mag_error = pmn_source[f'{band}_err']
                computed_mag_error = get_mag_error(corrected_source[f'{label}_flux_{band}'],
                                                   corrected_source[f'{label}_flux_error_{band}'])
                npt.assert_almost_equal(pmn_mag_error, computed_mag_error)

    def test_absent_filter_present_colour(self):
        """
        Test for SDSS_Doi_Std when the value for the filter is nan but the colour
        is present.
        """
        # Result should be nan for magnitude, fluxes and errors
        phot_system = PhotometricSystem.SDSS_Std
        label = phot_system.get_system_label()
        # Generate a dataframe with the input data
        values = [428798990699423104, float('NaN'), 1.948665e+01, 1.782151e+01, 1.701492e+01, 1.653498e+01,
                  -6.904391e-32, 5.766324e-31, 2.691271e-30, 5.593872e-30, 8.745204e-30, 3.407144e-32,
                  1.020666e-32, 1.911510e-32, 1.829784e-32, 3.118226e-32]
        data = pd.DataFrame(np.array([values]), columns=sdss_std_cols)
        corrected_data = apply_colour_equation(data, photometric_system=phot_system, save_file=False)
        columns_that_change = [f'{label}_mag_u', f'{label}_flux_u', f'{label}_flux_error_u']
        # Data that should remain unchanged
        static_data = data.drop(columns=columns_that_change)
        static_data = cast_output(static_data)
        static_corrected_data = corrected_data.drop(columns=columns_that_change)
        # Static corrected data is the output of my function
        # Static data is the manually generated dataframe
        pdt.assert_frame_equal(static_corrected_data, static_data, rtol=_rtol, atol=_atol)
        # Data that should have changed
        for column in columns_that_change:
            self.assertTrue(math.isnan(corrected_data[column].iloc[0]))

    def test_absent_band_absent_colour(self):
        # mag, fluxes, errors are set to nan
        phot_system = PhotometricSystem.SDSS_Std
        label = phot_system.get_system_label()
        values = [5882658689230693632, float('NaN'), float('NaN'), 2.164732e+01, 1.801127e+01, 1.493796e+01,
                  -1.065495e-32, -4.320473e-33, 7.936535e-32, 2.234461e-30, 3.806927e-29, 5.685276e-33, 7.746770e-34,
                  2.471102e-32, 1.745934e-32, 6.280337e-32]
        data = pd.DataFrame(np.array([values]), columns=sdss_std_cols)
        corrected_data = apply_colour_equation(data, photometric_system=phot_system, save_file=False)
        columns_that_change = [f'{label}_mag_u', f'{label}_flux_u', f'{label}_flux_error_u']
        # Data that should remain unchanged
        static_data = data.drop(columns=columns_that_change)
        static_data = cast_output(static_data)
        static_corrected_data = corrected_data.drop(columns=columns_that_change)
        pdt.assert_frame_equal(static_corrected_data, static_data, rtol=_rtol, atol=_atol)
        # Data that should have changed
        for column in columns_that_change:
            self.assertTrue(math.isnan(corrected_data[column].iloc[0]))

    def test_absent_colour_one_band(self):
        # mag, fluxes, errors are set to nan
        phot_system = PhotometricSystem.SDSS_Std
        label = phot_system.get_system_label()
        # Generate a dataframe with the input data
        values = [4154201362082430080, 2.235461e+01, np.nan, 1.975758e+01, 1.715846e+01, 1.451727e+01, 4.838556e-32,
                  -9.957407e-33, 4.524045e-31, 4.901128e-30, 5.608559e-29, 8.698059e-32, 2.798101e-33, 1.464481e-31,
                  5.201447e-32, 1.301941e-31]
        data = pd.DataFrame(np.array([values]), columns=sdss_std_cols)
        corrected_data = apply_colour_equation(data, photometric_system=phot_system, save_file=False)
        columns_that_change = [f'{label}_mag_u', f'{label}_flux_u', f'{label}_flux_error_u']
        # Data that should remain unchanged
        static_data = data.drop(columns=columns_that_change)
        static_data = cast_output(static_data)
        static_corrected_data = corrected_data.drop(columns=columns_that_change)
        pdt.assert_frame_equal(static_corrected_data, static_data, rtol=_rtol, atol=_atol)
        # Data that should have changed
        for column in columns_that_change:
            self.assertTrue(math.isnan(corrected_data[column].iloc[0]))

    def test_absent_colour_two_bands(self):
        phot_system = PhotometricSystem.SDSS_Std
        label = phot_system.get_system_label()
        # Generate a dataframe with the input data
        values = [123456789, 2.235461e+01, float('NaN'), float('NaN'), 1.715846e+01, 1.451727e+01, 4.838556e-32,
                  -9.957407e-33, -4.524045e-31, 4.901128e-30, 5.608559e-29, 8.698059e-32, 2.798101e-33, 1.464481e-31,
                  5.201447e-32, 1.301941e-31]
        data = pd.DataFrame(np.array([values]), columns=sdss_std_cols)
        corrected_data = apply_colour_equation(data, photometric_system=phot_system, save_file=False)
        columns_that_change = [f'{label}_mag_u', f'{label}_flux_u', f'{label}_flux_error_u']
        # Data that should remain unchanged
        static_data = data.drop(columns=columns_that_change)
        static_data = cast_output(static_data)
        static_corrected_data = corrected_data.drop(columns=columns_that_change)
        pdt.assert_frame_equal(static_corrected_data, static_data, rtol=_rtol, atol=_atol)
        # Data that should have changed
        for column in columns_that_change:
            self.assertTrue(math.isnan(corrected_data[column].iloc[0]))

    def test_wrong_input_type(self):
        with pytest.raises(ValueError):
            _ = apply_colour_equation(colour_eq_csv_file)
