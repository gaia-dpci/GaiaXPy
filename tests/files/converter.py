"""Reference files used by converter tests."""
from gaiaxpy.core.generic_functions import str_to_array
from tests.files.paths import solution_path

converter_sol_path = solution_path / 'converter_solution'

con_converters = {column: str_to_array for column in ['flux', 'flux_error']}
con_cov_converters = {column: str_to_array for column in ['flux', 'flux_error', 'covariance']}

con_sol_with_missing_sampling_path = converter_sol_path / 'with_missing_converter_solution_sampling.csv'
con_sol_with_cov_missing_sampling_path = (
        converter_sol_path / 'converter_with_covariance_missing_bp_solution_sampling.csv'
)
con_ref_sampled_csv_path = converter_sol_path / 'SampledMeanSpectrum.csv'
con_ref_sampled_truncated_csv_path = converter_sol_path / 'SampledMeanSpectrum_truncated.csv'
con_sol_mean_spectrum_csv_with_cov_path = converter_sol_path / 'converter_with_covariance_missing_bp_solution.csv'
con_sol_avro_0_60_481_path = converter_sol_path / 'converter_avro_solution_0_60_481.csv'
con_sol_csv_0_60_481_path = converter_sol_path / 'converter_solution_0_60_481.csv'
con_sol_with_missing_path = converter_sol_path / 'with_missing_converter_solution.csv'

no_corr_output_file = converter_sol_path / 'two_regular_sources_no_corr_converter_solution.csv'
with_corr_output_file = converter_sol_path / 'two_regular_sources_with_corr_converter_solution.csv'
