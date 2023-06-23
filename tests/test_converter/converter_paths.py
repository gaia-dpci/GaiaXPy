import pandas as pd

from gaiaxpy.config.paths import optimised_bases_file
from gaiaxpy.converter.config import load_config as load_con_config
from tests.files.paths import con_sol_avro_0_60_481_path, con_sol_csv_0_60_481_path, con_sol_with_missing_sampling_path,\
    con_sol_with_cov_missing_sampling_path, con_sol_with_missing_path, con_sol_mean_spectrum_csv_with_cov_path,\
    con_converters, con_cov_converters
from tests.utils.utils import pos_file_to_array, missing_bp_source_id

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
missing_solution_df = with_missing_solution_df[with_missing_solution_df['source_id'] ==
                                               missing_bp_source_id].reset_index(drop=True)
mean_spectrum_csv_with_cov_sol_df = pd.read_csv(con_sol_mean_spectrum_csv_with_cov_path, float_precision='high',
                                                converters=con_cov_converters)
converter_avro_solution_0_60_481_df = pd.read_csv(con_sol_avro_0_60_481_path, float_precision='high',
                                                  converters=con_converters)
converter_csv_solution_0_60_481_df = pd.read_csv(con_sol_csv_0_60_481_path, float_precision='high',
                                                 converters=con_converters)

"""
===================
  Optimised bases
===================
"""
optimised_bases_df = load_con_config(optimised_bases_file)
