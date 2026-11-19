"""Reference files used by calibrator tests."""
from gaiaxpy.core.generic_functions import str_to_array
from tests.files.paths import solution_path

calibrator_sol_path = solution_path / 'calibrator_solution'

cal_sol_default_sampling_path = calibrator_sol_path / 'calibrator_solution_default_sampling.csv'
sol_custom_sampling_path = calibrator_sol_path / 'calibrator_solution_custom_sampling.csv'
cal_sol_with_missing_sampling_path = calibrator_sol_path / 'with_missing_calibrator_solution_sampling.csv'
cal_sol_with_covariance_sampling_path = calibrator_sol_path / 'calibrate_with_covariance_solution_sampling.csv'

calibrator_sol_converters = {column: str_to_array for column in ['flux', 'flux_error']}
cal_sol_default_path = calibrator_sol_path / 'calibrator_solution_default.csv'
cal_sol_custom_path = calibrator_sol_path / 'calibrator_solution_custom.csv'
cal_sol_with_missing_path = calibrator_sol_path / 'with_missing_calibrator_solution.csv'
cal_sol_with_truncation_path = calibrator_sol_path / 'calibrator_solution_truncation_default.csv'
