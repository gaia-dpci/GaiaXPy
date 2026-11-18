import numpy as np

from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.required_columns import CORR_INPUT_COLUMNS, COV_INPUT_COLUMNS
from gaiaxpy.spectrum.utils import correlation_to_covariance_dr3int5
from tests.files.continuous import dr3_mean_spectra_avro_file, dr3_mean_spectra_csv_file

__BASE_COLUMNS = ['source_id', 'bp_coefficients', 'rp_coefficients', 'bp_n_parameters', 'rp_n_parameters',
                  'bp_standard_deviation', 'rp_standard_deviation']


def test_correlation_to_covariance():
    corr_parser = InternalContinuousParser(requested_columns=__BASE_COLUMNS + CORR_INPUT_COLUMNS)
    cov_parser = InternalContinuousParser(requested_columns=__BASE_COLUMNS + COV_INPUT_COLUMNS)
    # Parsed files
    parsed_correlation, _ = corr_parser.parse_file(dr3_mean_spectra_csv_file)
    parsed_covariance, _ = cov_parser.parse_file(dr3_mean_spectra_avro_file)
    for band in BANDS:
        correlation_matrix = parsed_correlation[f'{band}_coefficient_correlations'][0]
        formal_errors = parsed_correlation[f'{band}_coefficient_errors'][0]
        standard_deviation = parsed_correlation[f'{band}_standard_deviation'][0]
        reconstructed_covariance = correlation_to_covariance_dr3int5(correlation_matrix, formal_errors,
                                                                     standard_deviation)
        covariance_matrix = parsed_covariance[f'{band}_coefficient_covariances'][0]
        assert np.allclose(reconstructed_covariance, covariance_matrix, rtol=1e-6, atol=1e-3), \
            'The reconstructed covariance is different from the expected matrix.'
