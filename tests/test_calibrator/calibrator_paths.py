from os.path import join

import pandas as pd

from gaiaxpy.core.generic_functions import str_to_array
from tests.files.paths import files_path
from tests.utils.utils import pos_file_to_array

continuous_path = join(files_path, 'xp_continuous')
calibrator_sol_path = join(files_path, 'calibrator_solution')
solution_converters = dict([(column, lambda x: str_to_array(x)) for column in ['flux', 'flux_error']])

"""
============================
  Regular continuous files
============================
"""
mean_spectrum_avro = join(continuous_path, 'MeanSpectrumSolutionWithCov.avro')
mean_spectrum_csv = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')
mean_spectrum_fits = join(continuous_path, 'XP_CONTINUOUS_RAW.fits')
mean_spectrum_xml = join(continuous_path, 'XP_CONTINUOUS_RAW.xml')
mean_spectrum_xml_plain = join(continuous_path, 'XP_CONTINUOUS_RAW_plain.xml')

"""
====================================
  Continuous files with missing BP
====================================
"""
mean_spectrum_csv_with_missing = join(continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.csv')

"""
============================
  Tests sampling solutions
============================
"""
# Default model
sol_default_sampling = pos_file_to_array(join(calibrator_sol_path, 'calibrator_solution_default_sampling.csv'))
sol_custom_sampling = pos_file_to_array(join(calibrator_sol_path, 'calibrator_solution_custom_sampling.csv'))

# v211w model
sol_v211w_default_sampling = pos_file_to_array(join(calibrator_sol_path,
                                                    'calibrator_solution_v211w_default_sampling.csv'))
sol_v211w_custom_sampling = pos_file_to_array(join(calibrator_sol_path,
                                                   'calibrator_solution_v211w_custom_sampling.csv'))

# With missing
sol_with_missing_sampling = pos_file_to_array(join(calibrator_sol_path, 'with_missing_calibrator_solution_sampling.csv'))

# With covariance
sol_with_covariance_sampling = pos_file_to_array(join(files_path, 'calibrator_solution',
                                                      'calibrate_with_covariance_solution_sampling.csv'))

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