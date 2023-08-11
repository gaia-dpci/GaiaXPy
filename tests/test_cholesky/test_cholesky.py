import unittest
from os.path import join

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import get_chi2, get_inverse_covariance_matrix
from gaiaxpy.cholesky.cholesky import _get_inverse_square_root_covariance_matrix_aux, \
    get_inverse_square_root_covariance_matrix
from gaiaxpy.core.generic_functions import str_to_array, array_to_symmetric_matrix
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.paths import with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_xml_file, \
    mean_spectrum_csv_file
from tests.test_cholesky.cholesky_solutions import cholesky_solution, cholesky_sol_path, \
    inv_sqrt_cov_matrix_sol_df_no_missing_df, inv_sqrt_cov_matrix_sol_with_missing_df
from tests.utils.utils import parse_matrices

_rtol = 1e-05
_atol = 1e-05


class TestCholesky(unittest.TestCase):

    def test_inverse_covariance_matrix_from_file(self):
        inverse_df = get_inverse_covariance_matrix(with_missing_bp_xml_file)
        pdt.assert_frame_equal(inverse_df, cholesky_solution, rtol=_rtol, atol=_atol)

    def test_inverse_covariance_matrix_from_df_str(self):
        df = pd.read_csv(with_missing_bp_csv_file)
        inverse_df = get_inverse_covariance_matrix(df)
        pdt.assert_frame_equal(inverse_df, cholesky_solution, rtol=_rtol, atol=_atol)

    def test_inverse_covariance_matrix_file_from_df_numpy_array(self):
        df = pd.read_csv(with_missing_bp_csv_file)
        # Correlations and error should be NumPy array
        for column in ['bp_coefficient_correlations', 'bp_coefficient_errors', 'rp_coefficient_correlations',
                       'rp_coefficient_errors']:
            df[column] = df[column].map(str_to_array)
        for column in ['bp_coefficient_correlations', 'rp_coefficient_correlations']:
            df[column] = df[column].apply(lambda row: array_to_symmetric_matrix(row, 55))
        inverse_df = get_inverse_covariance_matrix(df)
        pdt.assert_frame_equal(inverse_df, cholesky_solution, rtol=_rtol, atol=_atol)

    def test_inverse_covariance_matrix_file_from_df_numpy_matrix(self):
        # Test completely parsed (arrays + matrices) dataframe
        df, _ = InputReader(with_missing_bp_csv_file, get_inverse_covariance_matrix).read()
        inverse_df = get_inverse_covariance_matrix(df)
        pdt.assert_frame_equal(inverse_df, cholesky_solution, rtol=_rtol, atol=_atol)

    def test_get_chi2(self):
        matrix = np.random.rand(55, 55)
        residuals = np.random.rand(55)
        output = get_chi2(matrix, residuals)
        self.assertIsInstance(output, float)

    def test_get_chi2_wrong_length(self):
        matrix = np.random.rand(55, 55)
        residuals = np.random.rand(54)
        with self.assertRaises(ValueError):
            get_chi2(matrix, residuals)

    def test_get_chi2_values(self):
        inv_sqrt_cov_df = get_inverse_square_root_covariance_matrix(mean_spectrum_csv_file)
        inv_sqrt_cov_row = inv_sqrt_cov_df[inv_sqrt_cov_df['source_id'] == 5853498713190525696].iloc[0]
        bp_inv_sqrt_cov = inv_sqrt_cov_row['bp_inverse_square_root_covariance_matrix']
        mock_residuals = np.array(list(range(55)))
        self.assertAlmostEqual(get_chi2(bp_inv_sqrt_cov, mock_residuals), 16655.037182417516, places=7)


class TestInverseSquareRootCovarianceMatrix(unittest.TestCase):

    def test_internal_inverse_square_root_covariance_matrix_no_missing_bands(self):
        parsed_input_data, extension = InputReader(mean_spectrum_csv_file,
                                                   get_inverse_square_root_covariance_matrix).read()
        output_columns = ['source_id', 'bp_inverse_square_root_covariance_matrix',
                          'rp_inverse_square_root_covariance_matrix']
        bands_output = []
        for b in BANDS:
            xp_errors = (parsed_input_data[f'{b}_coefficient_errors'] / parsed_input_data[f'{b}_standard_deviation'])
            xp_correlation_matrix = parsed_input_data[f'{b}_coefficient_correlations']
            band_output = map(_get_inverse_square_root_covariance_matrix_aux, xp_errors, xp_correlation_matrix)
            bands_output.append(band_output)
        output_list = [parsed_input_data['source_id']]
        for element in bands_output:
            output_list.append(element)
        output_df = pd.DataFrame(zip(*output_list), columns=output_columns)
        pdt.assert_frame_equal(output_df, inv_sqrt_cov_matrix_sol_df_no_missing_df)

    def test_internal_inverse_square_root_covariance_matrix_with_missing_bands(self):
        parsed_input_data, extension = InputReader(with_missing_bp_csv_file,
                                                   get_inverse_square_root_covariance_matrix).read()
        output_columns = ['source_id', 'bp_inverse_square_root_covariance_matrix',
                          'rp_inverse_square_root_covariance_matrix']
        bands_output = []
        for b in BANDS:
            xp_errors = (parsed_input_data[f'{b}_coefficient_errors'] / parsed_input_data[f'{b}_standard_deviation'])
            xp_correlation_matrix = parsed_input_data[f'{b}_coefficient_correlations']
            band_output = map(_get_inverse_square_root_covariance_matrix_aux, xp_errors, xp_correlation_matrix)
            bands_output.append(band_output)
        output_list = [parsed_input_data['source_id']]
        for element in bands_output:
            output_list.append(element)
        output_df = pd.DataFrame(zip(*output_list), columns=output_columns)
        pdt.assert_frame_equal(output_df, inv_sqrt_cov_matrix_sol_with_missing_df)

    # File input
    def test_external_inverse_square_root_covariance_matrix_no_missing_bands_both_bands_file_input(self):
        output_df = get_inverse_square_root_covariance_matrix(mean_spectrum_csv_file)
        pdt.assert_frame_equal(output_df, inv_sqrt_cov_matrix_sol_df_no_missing_df)

    def test_external_inverse_square_root_covariance_matrix_with_missing_bands_file_input(self):
        output_df = get_inverse_square_root_covariance_matrix(with_missing_bp_csv_file)
        pdt.assert_frame_equal(output_df, inv_sqrt_cov_matrix_sol_with_missing_df)

    # DF input
    def test_external_inverse_square_root_covariance_matrix_no_missing_bands_both_bands_df_input(self):
        output_df = get_inverse_square_root_covariance_matrix(mean_spectrum_csv_file)
        pdt.assert_frame_equal(output_df, inv_sqrt_cov_matrix_sol_df_no_missing_df)

    def test_external_inverse_square_root_covariance_matrix_with_missing_bands_df_input(self):
        output_df = get_inverse_square_root_covariance_matrix(with_missing_bp_csv_file)
        pdt.assert_frame_equal(output_df, inv_sqrt_cov_matrix_sol_with_missing_df)

    # Single band tests
    def test_external_inverse_square_root_covariance_matrix_no_missing_bands_bp_file_input(self):
        output_df = get_inverse_square_root_covariance_matrix(mean_spectrum_csv_file, band='BP')
        pdt.assert_frame_equal(output_df, inv_sqrt_cov_matrix_sol_df_no_missing_df[output_df.columns])

    def test_external_inverse_square_root_covariance_matrix_with_missing_bands_rp_file_input(self):
        output_df = get_inverse_square_root_covariance_matrix(with_missing_bp_ecsv_file, band=['rP'])
        pdt.assert_frame_equal(output_df, inv_sqrt_cov_matrix_sol_with_missing_df[output_df.columns])

    # One source ID
    def test_external_inverse_square_root_covariance_matrix_one_row_one_band_input(self):
        input_object = pd.read_csv(with_missing_bp_csv_file).iloc[[2]]  # Select just one row
        output = get_inverse_square_root_covariance_matrix(input_object, band='rP')
        # Almost equal as the solution file contains fewer decimals than the ones returned by the function
        npt.assert_array_almost_equal(
            output, inv_sqrt_cov_matrix_sol_with_missing_df['rp_inverse_square_root_covariance_matrix'].iloc[2])
