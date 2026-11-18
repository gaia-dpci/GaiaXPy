"""Reference files used by Cholesky tests."""
from tests.files.paths import solution_path

cholesky_sol_path = solution_path / 'cholesky_solution'
cholesky_solution_path = cholesky_sol_path / 'test_cholesky_solution.csv'
inv_sqrt_cov_matrix_no_missing_path = cholesky_sol_path / 'inv_sqrt_cov_matrix_no_missing_bands_solution.csv'
inv_sqrt_cov_matrix_with_missing_path = cholesky_sol_path / 'inv_sqrt_cov_matrix_with_missing_band_solution.csv'
inv_cov_with_missing_path = cholesky_sol_path / 'get_inv_cov_with_missing_bp.csv'
