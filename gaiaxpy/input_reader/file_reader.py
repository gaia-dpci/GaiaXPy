from gaiaxpy.file_parser.parse_external import ExternalParser
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser


def external():
    return ExternalParser()


def internal_continuous(mandatory_columns):
    return InternalContinuousParser(mandatory_columns=mandatory_columns)


def raise_error():
    raise ValueError('File parser not implemented. This function cannot receive a file as input.')


function_parser_dict = {'apply_colour_equation': raise_error,
                        'convert': internal_continuous,
                        '_calibrate': internal_continuous,
                        'calibrate': internal_continuous,
                        '_generate': internal_continuous,
                        'generate': internal_continuous,
                        'get_inverse_covariance_matrix': internal_continuous,
                        'get_inverse_square_root_covariance_matrix': internal_continuous,
                        'simulate_continuous': external,
                        'simulate_sampled': external}

# Mandatory columns for each tool (technically, xp_n_relevant_bases are optional depending on "truncation")
__CAL_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'bp_standard_deviation', 'bp_coefficients',
                        'bp_coefficient_errors', 'bp_coefficient_correlations', 'bp_n_relevant_bases',
                        'rp_n_parameters', 'rp_standard_deviation', 'rp_coefficients',
                        'rp_coefficient_errors', 'rp_coefficient_correlations', 'rp_n_relevant_bases']

__CON_MANDATORY_COLS = ['source_id', 'bp_basis_function_id', 'bp_n_parameters', 'bp_standard_deviation',
                        'bp_coefficients', 'bp_coefficient_errors', 'bp_coefficient_correlations',
                        'bp_n_relevant_bases', 'rp_basis_function_id', 'rp_n_parameters', 'rp_standard_deviation',
                        'rp_coefficients', 'rp_coefficient_errors', 'rp_coefficient_correlations', 'rp_n_relevant_bases']

__GEN_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'bp_standard_deviation', 'bp_coefficients',
                        'bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_n_parameters',
                        'rp_standard_deviation', 'rp_coefficients', 'rp_coefficient_errors',
                        'rp_coefficient_correlations']

__INV_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'bp_standard_deviation', 'bp_coefficient_errors',
                         'bp_coefficient_correlations', 'rp_n_parameters', 'rp_standard_deviation',
                         'rp_coefficient_errors', 'rp_coefficient_correlations']

MANDATORY_COLS = {'_calibrate': __CAL_MANDATORY_COLS, 'calibrate': __CAL_MANDATORY_COLS,
                  'convert': __CON_MANDATORY_COLS, 'generate': __GEN_MANDATORY_COLS,
                  'get_inverse_covariance_matrix': __INV_MANDATORY_COLS,
                  'get_inverse_square_root_covariance_matrix': __INV_MANDATORY_COLS}


class FileSelector(object):

    def __init__(self, function):
        self.function = function.__name__

    def select(self):
        mandatory_columns = MANDATORY_COLS[self.function]
        return function_parser_dict[self.function](mandatory_columns)
