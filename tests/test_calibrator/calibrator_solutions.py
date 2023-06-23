import pandas as pd

from tests.files.paths import cal_sol_default_sampling_path, sol_custom_sampling_path, cal_sol_v211w_default_sampling_path, \
    cal_sol_v211w_custom_sampling_path, cal_sol_with_missing_sampling_path, cal_sol_with_covariance_sampling_path, calibrator_sol_converters, \
    cal_sol_default_path, cal_sol_custom_path, cal_sol_v211w_default_path, cal_sol_v211w_custom_path, \
    cal_sol_with_missing_path, cal_sol_with_truncation_path
from tests.utils.utils import pos_file_to_array, missing_bp_source_id

"""
============================
  Sampling solutions
============================
"""
# Default model
sol_default_sampling_array = pos_file_to_array(cal_sol_default_sampling_path)
sol_custom_sampling_array = pos_file_to_array(sol_custom_sampling_path)
# v211w model
sol_v211w_default_sampling_array = pos_file_to_array(cal_sol_v211w_default_sampling_path)
sol_v211w_custom_sampling_array = pos_file_to_array(cal_sol_v211w_custom_sampling_path)
# With missing
sol_with_missing_sampling_array = pos_file_to_array(cal_sol_with_missing_sampling_path)
# With covariance
sol_with_covariance_sampling_array = pos_file_to_array(cal_sol_with_covariance_sampling_path)

"""
=====================
  Regular solutions
=====================
"""
# Default model
solution_default_df = pd.read_csv(cal_sol_default_path, float_precision='high', converters=calibrator_sol_converters)
solution_custom_df = pd.read_csv(cal_sol_custom_path, float_precision='high', converters=calibrator_sol_converters)
# v211w model
solution_v211w_default_df = pd.read_csv(cal_sol_v211w_default_path, float_precision='high',
                                        converters=calibrator_sol_converters)
solution_v211w_custom_df = pd.read_csv(cal_sol_v211w_custom_path, float_precision='high',
                                       converters=calibrator_sol_converters)
# With missing
with_missing_solution_df = pd.read_csv(cal_sol_with_missing_path, float_precision='high',
                                       converters=calibrator_sol_converters)
# Isolated missing
missing_solution_df = with_missing_solution_df[with_missing_solution_df['source_id'] ==
                                               missing_bp_source_id].reset_index(drop=True)
# With truncation
truncation_default_solution_df = pd.read_csv(cal_sol_with_truncation_path, float_precision='high',
                                             converters=calibrator_sol_converters)
