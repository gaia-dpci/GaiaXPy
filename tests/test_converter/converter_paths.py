import pandas as pd

from gaiaxpy.config.paths import hermite_bases_file
from gaiaxpy.converter.config import parse_config as parse_con_config
from tests.files.paths import (con_converters, con_cov_converters, con_sol_avro_0_60_481_path,
                               con_sol_csv_0_60_481_path, con_sol_mean_spectrum_csv_with_cov_path,
                               con_sol_with_cov_missing_sampling_path,
                               con_sol_with_missing_path, con_sol_with_missing_sampling_path)
from tests.utils.utils import pos_file_to_array, missing_bp_source_id


def replace_empty_array_with_none(value):
    import numpy as np
    if (isinstance(value, list) or isinstance(value, np.ndarray)) and len(value) == 0:
        return None
    else:
        return value


"""
============================
  Sampling solutions
============================
"""
with_missing_solution_sampling = pos_file_to_array(con_sol_with_missing_sampling_path)
with_cov_missing_sampling = pos_file_to_array(con_sol_with_cov_missing_sampling_path)

"""
====================
  Regular solutions
=====================
"""
with_missing_solution_df = pd.read_csv(con_sol_with_missing_path, converters=con_converters)
for col in ['flux', 'flux_error']:
    with_missing_solution_df[col] = with_missing_solution_df[col].apply(replace_empty_array_with_none)
missing_solution_df = with_missing_solution_df[with_missing_solution_df['source_id'] ==
                                               missing_bp_source_id].reset_index(drop=True)
mean_spectrum_csv_with_cov_sol_df = pd.read_csv(con_sol_mean_spectrum_csv_with_cov_path, float_precision='round_trip',
                                                converters=con_cov_converters)
for col in ['flux', 'flux_error', 'covariance']:
    mean_spectrum_csv_with_cov_sol_df[col] = mean_spectrum_csv_with_cov_sol_df[col].apply(replace_empty_array_with_none)
converter_avro_solution_0_60_481_df = pd.read_csv(con_sol_avro_0_60_481_path, float_precision='round_trip',
                                                  converters=con_converters)
converter_csv_solution_0_60_481_df = pd.read_csv(con_sol_csv_0_60_481_path, float_precision='round_trip',
                                                 converters=con_converters)

"""
===================
  Optimised bases
===================
"""
optimised_bases_df = parse_con_config(hermite_bases_file)
