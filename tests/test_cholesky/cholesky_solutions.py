from os.path import join

import pandas as pd

from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.core.satellite import BANDS
from tests.files.paths import files_path, with_missing_bp_csv_file
from tests.utils.utils import parse_matrices, missing_bp_source_id

cholesky_sol_path = join(files_path, 'cholesky_solution')

"""
============================
  Solution files
============================
"""
cholesky_converters = dict([(column, lambda x: parse_matrices(x)) for column in ['bp_inverse_covariance',
                                                                                 'rp_inverse_covariance']])
cholesky_solution = pd.read_csv(join(cholesky_sol_path, 'test_cholesky_solution.csv'), float_precision='high',
                                converters=cholesky_converters)

solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
# No missing inv sqrt
inv_sqrt_cov_matrix_sol_df_no_missing_df = pd.read_csv(join(cholesky_sol_path,
                                                            'inv_sqrt_cov_matrix_no_missing_bands_solution.csv'),
                                                       converters=solution_converters)
# With missing inv sqrt
inv_sqrt_cov_matrix_sol_with_missing_df = pd.read_csv(join(cholesky_sol_path,
                                                           'inv_sqrt_cov_matrix_with_missing_band_solution.csv'),
                                                      converters=solution_converters)
# With missing cov
inv_cov_with_missing_path = join(cholesky_sol_path, 'get_inv_cov_with_missing_bp.csv')
inv_cov_with_missing_df = pd.read_csv(inv_cov_with_missing_path,
                                      converters=dict([(column, lambda x: parse_matrices(x)) for column in
                                                       [f'{band}_inverse_covariance' for band in BANDS]]))
# With missing
input_array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficients',
                       'rp_coefficient_errors', 'rp_coefficient_correlations']
with_missing_df = pd.read_csv(with_missing_bp_csv_file, converters=dict([(column, lambda x: str_to_array(x)) for
                                                                         column in input_array_columns]))
isolated_missing_df = with_missing_df[with_missing_df['source_id'] == missing_bp_source_id]
