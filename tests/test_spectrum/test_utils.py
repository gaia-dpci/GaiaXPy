import unittest
from os import path

import numpy as np

from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.utils import _correlation_to_covariance_dr3int5
from tests.files.paths import files_path, mean_spectrum_avro_file, mean_spectrum_csv_file

# Parsers
parser = InternalContinuousParser()
# Parsed files
parsed_correlation, _ = parser._parse(mean_spectrum_csv_file)
parsed_covariance, _ = parser._parse(mean_spectrum_avro_file)

# Tolerances
abs_tol = 1.e-3
rel_tol = 1.e-6


class TestUtils(unittest.TestCase):

    def test_correlation_to_covariance_bp(self):
        correlation_matrix = parsed_correlation[f'{BANDS.bp}_coefficient_correlations'][0]
        formal_errors = parsed_correlation[f'{BANDS.bp}_coefficient_errors'][0]
        standard_deviation = parsed_correlation[f'{BANDS.bp}_standard_deviation'][0]
        reconstructed_covariance = _correlation_to_covariance_dr3int5(
            correlation_matrix, formal_errors, standard_deviation)
        covariance_matrix = parsed_covariance[f'{BANDS.bp}_coefficient_covariances'][0]
        self.assertTrue(np.allclose(reconstructed_covariance, covariance_matrix, rel_tol, abs_tol),
                        "The reconstructed covariance is different from the expected matrix.")

    def test_correlation_to_covariance_rp(self):
        correlation_matrix = parsed_correlation[f'{BANDS.rp}_coefficient_correlations'][0]
        formal_errors = parsed_correlation[f'{BANDS.rp}_coefficient_errors'][0]
        standard_deviation = parsed_correlation[f'{BANDS.rp}_standard_deviation'][0]
        reconstructed_covariance = _correlation_to_covariance_dr3int5(
            correlation_matrix, formal_errors, standard_deviation)
        covariance_matrix = parsed_covariance[f'{BANDS.rp}_coefficient_covariances'][0]
        self.assertTrue(np.allclose(reconstructed_covariance, covariance_matrix, rel_tol, abs_tol),
                        "The reconstructed covariance is different from the expected matrix.")
