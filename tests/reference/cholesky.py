import pandas as pd

from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.core.satellite import BANDS
from tests.files.cholesky import (cholesky_solution_path, inv_cov_with_missing_path,
                                  inv_sqrt_cov_matrix_no_missing_path,
                                  inv_sqrt_cov_matrix_with_missing_path)
from tests.files.continuous import dr3_with_missing_bp_csv_file
from tests.utils.utils import parse_matrices, dr3_missing_bp_source_id

"""
============================
  Solution files
============================
"""
cholesky_converters = dict([(column, lambda x: parse_matrices(x)) for column in ['bp_inverse_covariance',
                                                                                 'rp_inverse_covariance']])
cholesky_solution = pd.read_csv(cholesky_solution_path,
                                converters=cholesky_converters, **CSV_FLOAT_PRECISION_KWARGS)

solution_array_columns = [f'{band}_inverse_square_root_covariance_matrix' for band in BANDS]
solution_converters = dict([(column, lambda x: parse_matrices(x)) for column in solution_array_columns])
# No missing inv sqrt
inv_sqrt_cov_matrix_sol_no_missing_df = pd.read_csv(inv_sqrt_cov_matrix_no_missing_path, converters=solution_converters,
                                                    **CSV_FLOAT_PRECISION_KWARGS)
# With missing inv sqrt
inv_sqrt_cov_matrix_sol_with_missing_df = pd.read_csv(inv_sqrt_cov_matrix_with_missing_path,
                                                      converters=solution_converters, **CSV_FLOAT_PRECISION_KWARGS)
# With missing cov
inv_cov_with_missing_df = pd.read_csv(inv_cov_with_missing_path,
                                      converters=dict([(column, lambda x: parse_matrices(x)) for column in
                                                       [f'{band}_inverse_covariance' for band in BANDS]]),
                                      **CSV_FLOAT_PRECISION_KWARGS)
# With missing
input_array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficients',
                       'rp_coefficient_errors', 'rp_coefficient_correlations']
with_missing_df = pd.read_csv(dr3_with_missing_bp_csv_file, converters=dict([(column, lambda x: str_to_array(x)) for
                                                                             column in input_array_columns]),
                              **CSV_FLOAT_PRECISION_KWARGS)
isolated_missing_df = with_missing_df[with_missing_df['source_id'] == dr3_missing_bp_source_id]
