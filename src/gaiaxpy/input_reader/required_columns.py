__CAL_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'bp_standard_deviation', 'rp_n_parameters',
                        'rp_standard_deviation']
__CON_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'bp_standard_deviation', 'rp_n_parameters',
                        'rp_standard_deviation']
__GEN_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'bp_standard_deviation', 'rp_n_parameters',
                        'rp_standard_deviation']
__INV_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'rp_n_parameters', 'bp_standard_deviation',
                        'rp_standard_deviation']

COV_INPUT_COLUMNS = ['bp_coefficient_covariances', 'rp_coefficient_covariances']
CORR_INPUT_COLUMNS = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations',
                      'rp_coefficients', 'rp_coefficient_errors', 'rp_coefficient_correlations']

MANDATORY_INPUT_COLS = {'_apply_colour_equation': __GEN_MANDATORY_COLS, '_apply_error_correction': __GEN_MANDATORY_COLS,
                        '_calibrate': __CAL_MANDATORY_COLS, 'calibrate': __CAL_MANDATORY_COLS,
                        '_convert': __CON_MANDATORY_COLS, 'convert': __CON_MANDATORY_COLS,
                        '_generate': __GEN_MANDATORY_COLS, 'generate': __GEN_MANDATORY_COLS,
                        'get_inverse_covariance_matrix': __INV_MANDATORY_COLS,
                        'get_inverse_square_root_covariance_matrix': __INV_MANDATORY_COLS}

TRUNCATION_COLS = ['bp_n_relevant_bases', 'rp_n_relevant_bases']

# Output columns
CAL_CORR_OUTPUT_COLS = ['correlation']
__CAL_OUTPUT_COLS = ['source_id', 'flux', 'flux_error']

CON_CORR_OUTPUT_COLS = ['correlation', 'standard_deviation']
__CON_OUTPUT_COLS = ['source_id', 'xp', 'flux', 'flux_error']

# Generator columns are not fixed but variable, depending on the systems involved; no correlation columns either.

# Whether all columns are present depends on the band(s) being requested
__INV_OUTPUT_COLS = ['source_id', 'bp_inverse_covariance', 'rp_inverse_covariance']
__INV_SQRT_OUTPUT_COLS = ['source_id', 'bp_inverse_square_root_covariance_matrix',
                          'rp_inverse_square_root_covariance_matrix']

# apply_error_correction should output the same columns that were received in the input, and will not accept the
# additional_columns argument
