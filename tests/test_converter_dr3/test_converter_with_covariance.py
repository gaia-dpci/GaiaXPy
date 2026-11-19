import numpy.testing as npt

from gaiaxpy import convert
from gaiaxpy.core.generic_functions import correlation_to_covariance
from gaiaxpy.core.generic_variables import RELEASES
from tests.files.continuous import dr3_with_missing_bp_csv_file
from tests.reference.converter import mean_spectrum_csv_with_cov_sol_df, with_cov_missing_sampling
from tests.utils.utils import assert_dfs_equal


def test_with_covariance():
    output_spectra, sampling = convert(dr3_with_missing_bp_csv_file, with_correlation=True, save_file=False,
                                       release=RELEASES.dr3)
    output_spectra['covariance'] = output_spectra.apply(lambda row: correlation_to_covariance(
        row['correlation'], row['flux_error'], row['standard_deviation']), axis=1)
    output_spectra = output_spectra.drop(columns=['correlation', 'standard_deviation'])
    assert_dfs_equal(output_spectra, mean_spectrum_csv_with_cov_sol_df, atol=1e-10, rtol=1e-10)
    npt.assert_array_equal(sampling, with_cov_missing_sampling)
