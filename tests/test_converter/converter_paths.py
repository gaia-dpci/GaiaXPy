from configparser import ConfigParser
from os.path import join

import pandas as pd

from gaiaxpy.config.paths import config_path
from gaiaxpy.converter.config import load_config as load_con_config
from gaiaxpy.core.generic_functions import str_to_array
from tests.files.paths import files_path, continuous_path
from tests.utils.utils import pos_file_to_array, missing_bp_source_id

converter_sol_path = join(files_path, 'converter_solution')
"""
==========================
Regular continuous files
==========================
"""
converter_avro_solution_0_60_481_df = pd.read_csv(join(converter_sol_path, 'converter_avro_solution_0_60_481.csv'),
                                                  float_precision='high', converters=dict([(
        column, lambda x: str_to_array(x)) for column in ['flux', 'flux_error']]))
converter_csv_solution_0_60_481_df = pd.read_csv(join(converter_sol_path, 'converter_solution_0_60_481.csv'),
                                                 float_precision='high', converters=dict([(
        column, lambda x: str_to_array(x)) for column in ['flux', 'flux_error']]))

"""
============================
  Sampling solutions
============================
"""
with_missing_solution_sampling = pos_file_to_array(join(converter_sol_path,
                                                        'with_missing_converter_solution_sampling.csv'))
missing_band_sampling_solution = join(converter_sol_path, 'missing_band_default_sampling_solution.csv')

"""
==================
  Solution files
==================
"""
with_missing_solution_df = pd.read_csv(join(converter_sol_path, 'with_missing_converter_solution.csv'),
                                       converters=dict([(column, lambda x: str_to_array(x)) for column in
                                                        ['flux', 'flux_error']]))
missing_solution_df = with_missing_solution_df[with_missing_solution_df['source_id'] ==
                                               missing_bp_source_id].reset_index(drop=True)

# Files to compare the sampled spectrum with value by value without/with truncation applied
ref_sampled_csv = join(converter_sol_path, 'SampledMeanSpectrum.csv')
ref_sampled_truncated_csv = join(converter_sol_path, 'SampledMeanSpectrum_truncated.csv')

mean_spectrum_csv_with_cov_sol = join(converter_sol_path, 'converter_with_covariance_missing_bp_solution.csv')
mean_spectrum_csv_with_cov_sol_df = pd.read_csv(mean_spectrum_csv_with_cov_sol, float_precision='high',
                                                converters={key: (lambda x: str_to_array(x)) for key in
                                                            ['flux', 'flux_error', 'covariance']})

"""
===================
  Optimised bases
===================
"""
configparser = ConfigParser()
configparser.read(join(config_path, 'config.ini'))
config_file = join(config_path, configparser.get('converter', 'optimised_bases'))
optimised_bases_df = load_con_config(config_file)
