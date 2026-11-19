"""Configuration and reference files used by generator tests."""
import numpy as np

from tests.files.paths import config_path, solution_path

generator_sol_path = solution_path / 'generator_solution'
dr3_generator_sol_path = generator_sol_path / 'dr3'
gen_missing_band_sol_path = dr3_generator_sol_path / 'generator_missing_band_solution.csv'
no_correction_solution_path = dr3_generator_sol_path / 'generator_solution_with_missing_BP.csv'
correction_solution_path = dr3_generator_sol_path / 'generator_solution_with_missing_BP_error_correction.csv'

phot_system_specs_path = solution_path / 'PhotometricSystemSpecs.csv'
phot_system_specs_converters = {
    'bands': lambda x: x[1:-1].split(','),
    'zero_points': lambda y: np.array(y[1:-1].split(',')).astype(float),
}

additional_filters_dir = config_path / 'additional_filters'
additional_filters_dup_dir = config_path / 'additional_filters_duplicate'
additional_filters_mixed_release_dir = config_path / 'additional_filters_mixed_release'
generator_truncation_dir = config_path / 'generator_truncation'
