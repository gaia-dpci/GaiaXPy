import numpy as np
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.utils import _correlation_to_covariance_dr3int5

from tests.files.paths import mean_spectrum_avro_file, mean_spectrum_csv_file


def test_correlation_to_covariance():
    parser = InternalContinuousParser()
    # Parsed files
    parsed_correlation, _ = parser.parse_file(mean_spectrum_csv_file)
    parsed_covariance, _ = parser.parse_file(mean_spectrum_avro_file)
    for band in BANDS:
        correlation_matrix = parsed_correlation[f'{band}_coefficient_correlations'][0]
        formal_errors = parsed_correlation[f'{band}_coefficient_errors'][0]
        standard_deviation = parsed_correlation[f'{band}_standard_deviation'][0]
        reconstructed_covariance = _correlation_to_covariance_dr3int5(correlation_matrix, formal_errors,
                                                                      standard_deviation)
        covariance_matrix = parsed_covariance[f'{band}_coefficient_covariances'][0]
        assert np.allclose(reconstructed_covariance, covariance_matrix, rtol=1e-6, atol=1e-3), \
            'The reconstructed covariance is different from the expected matrix.'
