import numpy.testing as npt
import pandas.testing as pdt
from gaiaxpy import convert
from gaiaxpy.core.generic_functions import correlation_to_covariance

from tests.files.paths import with_missing_bp_csv_file
from tests.test_converter.converter_paths import mean_spectrum_csv_with_cov_sol_df, with_cov_missing_sampling


def test_with_covariance():
    output_spectra, sampling = convert(with_missing_bp_csv_file, with_correlation=True, save_file=False)
    output_spectra['covariance'] = output_spectra.apply(lambda row: correlation_to_covariance(
        row['correlation'], row['flux_error'], row['standard_deviation']), axis=1)
    output_spectra = output_spectra.drop(columns=['correlation', 'standard_deviation'])
    pdt.assert_frame_equal(output_spectra, mean_spectrum_csv_with_cov_sol_df, atol=1e-10, rtol=1e-10)
    npt.assert_array_equal(sampling, with_cov_missing_sampling)
