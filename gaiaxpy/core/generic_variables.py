pbar_colour = '#509faf'
pbar_message = {'calibrator': 'Calibrating data', 'converter': 'Converting data'}
pbar_units = {'calibrator': 'spec', 'colour_eq': 'syst', 'converter': 'spec', 'correction': 'syst',
              'photometry': 'spec', 'simulator': 'row'}

# Columns required by internal continuous, we want to avoid reading columns we aren't going to use
INTERNAL_CONT_COLS = ['source_id', 'bp_basis_function_id', 'bp_n_parameters', 'bp_standard_deviation',
                      'bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations', 'bp_n_relevant_bases',
                      'rp_basis_function_id', 'rp_n_parameters', 'rp_standard_deviation', 'rp_coefficients',
                      'rp_coefficient_errors', 'rp_coefficient_correlations', 'rp_n_relevant_bases']
