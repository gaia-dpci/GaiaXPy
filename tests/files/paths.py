from os.path import abspath, dirname, join

import numpy as np

from gaiaxpy.core.generic_functions import str_to_array

files_path = abspath(join(dirname(__file__)))
input_reader_solution_path = join(files_path, 'input_reader_solution.csv')

"""
=======================
  Input spectra files
=======================
"""
# Load XP continuous file
continuous_path = join(files_path, 'xp_continuous')
# Regular mean spectra files
mean_spectrum_avro_file = join(continuous_path, 'MeanSpectrumSolutionWithCov.avro')
mean_spectrum_csv_file = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')
mean_spectrum_ecsv_file = join(continuous_path, 'XP_CONTINUOUS_RAW.ecsv')
mean_spectrum_fits_file = join(continuous_path, 'XP_CONTINUOUS_RAW.fits')
mean_spectrum_xml_file = join(continuous_path, 'XP_CONTINUOUS_RAW.xml')
mean_spectrum_xml_plain_file = join(continuous_path, 'XP_CONTINUOUS_RAW_plain.xml')
# Three sources including the one without BP
with_missing_bp_csv_file = join(continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
with_missing_bp_ecsv_file = join(continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.ecsv')
with_missing_bp_fits_file = join(continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.fits')
with_missing_bp_xml_file = join(continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.xml')
with_missing_bp_xml_plain_file = join(continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP_plain.xml')
# The missing BP source isolated
missing_bp_csv_file = join(continuous_path, 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.csv')
missing_bp_ecsv_file = join(continuous_path, 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.ecsv')
missing_bp_fits_file = join(continuous_path, 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.fits')
missing_bp_xml_file = join(continuous_path, 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.xml')
missing_bp_xml_plain_file = join(continuous_path, 'XP_CONTINUOUS_RAW_missing_BP_plain_dr3int6.xml')
# Colour equation
colour_eq_csv_file = join(continuous_path, 'XP_CONTINUOUS_RAW_colour_eq_dr3int6.csv')

"""
==================
  Solution paths
==================
"""
output_sol_path = join(files_path, 'output_solution')  # Read the expected solution to compare with the output files
calibrator_sol_path = join(files_path, 'calibrator_solution')
colour_eq_sol_path = join(files_path, 'colour_equation')
converter_sol_path = join(files_path, 'converter_solution')
generator_sol_path = join(files_path, 'generator_solution')
corrected_error_sol_path = join(files_path, 'error_correction_solution')

"""
========================================
  Calibrator samplings solutions paths
========================================
"""
# Default model
cal_sol_default_sampling_path = join(calibrator_sol_path, 'calibrator_solution_default_sampling.csv')
sol_custom_sampling_path = join(calibrator_sol_path, 'calibrator_solution_custom_sampling.csv')
# v211w model
cal_sol_v211w_default_sampling_path = join(calibrator_sol_path, 'calibrator_solution_v211w_default_sampling.csv')
cal_sol_v211w_custom_sampling_path = join(calibrator_sol_path, 'calibrator_solution_v211w_custom_sampling.csv')
# With missing
cal_sol_with_missing_sampling_path = join(calibrator_sol_path, 'with_missing_calibrator_solution_sampling.csv')
# With covariance
cal_sol_with_covariance_sampling_path = join(calibrator_sol_path, 'calibrate_with_covariance_solution_sampling.csv')

"""
======================================
  Calibrator regular solutions paths
======================================
"""
# Calibrator solution converters
calibrator_sol_converters = dict([(column, lambda x: str_to_array(x)) for column in ['flux', 'flux_error']])
# Default model
cal_sol_default_path = join(calibrator_sol_path, 'calibrator_solution_default.csv')
cal_sol_custom_path = join(calibrator_sol_path, 'calibrator_solution_custom.csv')
# v211w model
cal_sol_v211w_default_path = join(calibrator_sol_path, 'calibrator_solution_v211w_default.csv')
cal_sol_v211w_custom_path = join(calibrator_sol_path, 'calibrator_solution_v211w_custom.csv')
# With missing
cal_sol_with_missing_path = join(calibrator_sol_path, 'with_missing_calibrator_solution.csv')
# With truncation
cal_sol_with_truncation_path = join(calibrator_sol_path, 'calibrator_solution_truncation_default.csv')

"""
===============================
Colour equation solution path
===============================
"""
col_eq_sol_johnson_path = join(colour_eq_sol_path, 'Landolt_Johnson_Ucorr_v375wiv142r_SAMPLE.csv')

"""
========================================
  Converter samplings solutions paths
========================================
"""
con_sol_missing_band_sampling_path = join(converter_sol_path, 'missing_band_default_sampling_solution.csv')
con_sol_with_missing_sampling_path = join(converter_sol_path, 'with_missing_converter_solution_sampling.csv')
con_sol_with_cov_missing_sampling_path = join(converter_sol_path,
                                              'converter_with_covariance_missing_bp_solution_sampling.csv')

"""
===================================
Converter regular solutions paths
===================================
"""
con_converters=dict([(column, lambda x: str_to_array(x)) for column in ['flux', 'flux_error']])
con_cov_converters={key: (lambda x: str_to_array(x)) for key in ['flux', 'flux_error', 'covariance']}
# Files to compare the sampled spectrum with value by value without/with truncation applied
con_ref_sampled_csv_path = join(converter_sol_path, 'SampledMeanSpectrum.csv')
con_ref_sampled_truncated_csv_path = join(converter_sol_path, 'SampledMeanSpectrum_truncated.csv')
con_sol_mean_spectrum_csv_with_cov_path = join(converter_sol_path,
                                               'converter_with_covariance_missing_bp_solution.csv')
con_sol_avro_0_60_481_path = join(converter_sol_path, 'converter_avro_solution_0_60_481.csv')
con_sol_csv_0_60_481_path = join(converter_sol_path, 'converter_solution_0_60_481.csv')
con_sol_with_missing_path = join(converter_sol_path, 'with_missing_converter_solution.csv')

"""
============================
  Generator solution paths
============================
"""
gen_missing_band_sol_path = join(generator_sol_path, 'generator_missing_band_solution.csv')
no_correction_solution_path = join(generator_sol_path, 'generator_solution_with_missing_BP.csv')
correction_solution_path = join(generator_sol_path, 'generator_solution_with_missing_BP_error_correction.csv')
phot_system_specs_converters = {'bands': lambda x: x[1:-1].split(','),
                                'zero_points': lambda y: np.array(y[1:-1].split(',')).astype(float)}
phot_system_specs_path = join(files_path, 'PhotometricSystemSpecs.csv')

"""
================================
  Mini files (first test files)
=================================
"""
mini_path = join(files_path, 'mini_files')
mini_csv_file = join(mini_path, 'SPSS_mini.csv')
mini_fits_file = join(mini_path, 'XP_SPECTRA_RAW_mini.fits')
mini_xml_file = join(mini_path, 'XP_SPECTRA_RAW_mini.xml')
no_ext_file = join(files_path, 'no_extension_file')

"""
=====================
  Other input paths
=====================
"""
phot_with_nan_path = join(files_path, 'phot_with_nan.csv')
