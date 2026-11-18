"""Input and reference files used by error-correction tests."""
from tests.files.paths import input_files_path, solution_path

phot_with_nan_path = input_files_path / 'phot_with_nan.csv'
corrected_error_sol_path = solution_path / 'error_correction_solution'
corrected_error_solution_path = corrected_error_sol_path / 'corrected_errors_solution.csv'
phot_with_nan_corrected_sol_path = corrected_error_sol_path / 'phot_with_nan_corrected.csv'
