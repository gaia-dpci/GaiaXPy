
# Mandatory columns for each tool (technically, xp_n_relevant_bases are optional depending on "truncation")
__CAL_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'bp_standard_deviation', 'bp_n_relevant_bases',
                        'rp_n_parameters', 'rp_standard_deviation', 'rp_n_relevant_bases']
__CON_MANDATORY_COLS = ['source_id', 'bp_basis_function_id', 'bp_n_parameters', 'bp_standard_deviation',
                        'bp_n_relevant_bases', 'rp_basis_function_id', 'rp_n_parameters', 'rp_standard_deviation',
                        'rp_n_relevant_bases']
__GEN_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'bp_standard_deviation', 'rp_n_parameters',
                        'rp_standard_deviation']
__INV_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'rp_n_parameters', 'bp_standard_deviation',
                        'rp_standard_deviation']

COVARIANCE_COLUMNS = ['bp_coefficient_covariances', 'rp_coefficient_covariances']
CORRELATIONS_COLUMNS = ['bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations',
                        'rp_coefficients', 'rp_coefficient_errors', 'rp_coefficient_correlations']

# External apply functions (the ones not prefixed by "_") do not have mandatory columns as they receive photometries
# In these cases, the columns depend on the systems in the photometry itself
MANDATORY_COLS = {'_apply_colour_equation': __GEN_MANDATORY_COLS, '_apply_error_correction': __GEN_MANDATORY_COLS,
                  '_calibrate': __CAL_MANDATORY_COLS, 'calibrate': __CAL_MANDATORY_COLS,
                  'convert': __CON_MANDATORY_COLS, 'generate': __GEN_MANDATORY_COLS,
                  'get_inverse_covariance_matrix': __INV_MANDATORY_COLS,
                  'get_inverse_square_root_covariance_matrix': __INV_MANDATORY_COLS}
