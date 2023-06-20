from os.path import join

import pandas as pd

from gaiaxpy.core.generic_functions import str_to_array
from tests.files.paths import calibrator_sol_path, sol_default_sampling, sol_custom_sampling, \
    sol_v211w_default_sampling, sol_v211w_custom_sampling, sol_with_missing_sampling, sol_with_covariance_sampling
from tests.utils.utils import pos_file_to_array

solution_converters = dict([(column, lambda x: str_to_array(x)) for column in ['flux', 'flux_error']])

"""
============================
  Sampling solutions
============================
"""
# Default model
sol_default_sampling_array = pos_file_to_array(sol_default_sampling)
sol_custom_sampling_array = pos_file_to_array(sol_custom_sampling)

# v211w model
sol_v211w_default_sampling_array = pos_file_to_array(sol_v211w_default_sampling)
sol_v211w_custom_sampling_array = pos_file_to_array(sol_v211w_custom_sampling)

# With missing
sol_with_missing_sampling_array = pos_file_to_array(sol_with_missing_sampling)

# With covariance
sol_with_covariance_sampling_array = pos_file_to_array(sol_with_covariance_sampling)

"""
===========================
  Tests regular solutions
===========================
"""
# Default model
solution_default_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_default.csv'), float_precision='high',
                                  converters=solution_converters)
solution_custom_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_custom.csv'), float_precision='high',
                                 converters=solution_converters)

# v211w model
solution_v211w_default_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_v211w_default.csv'),
                                        float_precision='high', converters=solution_converters)
solution_v211w_custom_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_v211w_custom.csv'),
                                       float_precision='high', converters=solution_converters)

# With missing
with_missing_solution_df = pd.read_csv(join(calibrator_sol_path, 'with_missing_calibrator_solution.csv'),
                                       converters=solution_converters)
