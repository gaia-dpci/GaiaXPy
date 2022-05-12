"""
utils.py
====================================
Module containing auxiliary functions of the parsers.
"""

import operator
from functools import reduce


def _get_from_dict(dictionary, map):
    try:
        return reduce(operator.getitem, map, dictionary)
    except TypeError:
        return None


# This dictionary contains the mapping from the usual CSV fields to the AVRO fields.
_csv_to_avro_map = {'source_id': ['sourceId'],
                    'rp_n_rejected_measurements': ['rpSpec', 'solution', 'numberOfRejectedMeasurements'],
                    'rp_chi_squared': ['rpSpec', 'solution', 'chiSquared'],
                    'rp_degrees_of_freedom': ['rpSpec', 'solution', 'degreesOfFreedom'],
                    'rp_n_parameters': ['rpSpec', 'solution', 'numberOfParameters'],
                    'rp_standard_deviation': ['rpSpec', 'solution', 'standardDeviation'],
                    'rp_n_measurements': ['rpSpec', 'solution', 'numberOfMeasurements'],
                    'rp_n_relevant_bases': ['rpSpec', 'NRelevantBases'],
                    'rp_basis_function_id': ['rpSpec', 'basisFunctionSetDefId'],
                    'rp_num_of_transits': ['rpNumOfTransits'],
                    'bp_n_rejected_measurements': ['bpSpec', 'solution', 'numberOfRejectedMeasurements'],
                    'bp_chi_squared': ['bpSpec', 'solution', 'chiSquared'],
                    'bp_degrees_of_freedom': ['bpSpec', 'solution', 'degreesOfFreedom'],
                    'bp_n_parameters': ['bpSpec', 'solution', 'numberOfParameters'],
                    'bp_standard_deviation': ['bpSpec', 'solution', 'standardDeviation'],
                    'bp_n_measurements': ['bpSpec', 'solution', 'numberOfMeasurements'],
                    'bp_n_relevant_bases': ['bpSpec', 'NRelevantBases'],
                    'bp_basis_function_id': ['bpSpec', 'basisFunctionSetDefId'],
                    'rp_num_of_blended_transits': ['rpNumOfBlendedTransits'],
                    'bp_num_of_transits': ['bpNumOfTransits'],
                    'bp_num_of_contaminated_transits': ['bpNumOfContaminatedTransits'],
                    'rp_num_of_contaminated_transits': ['rpNumOfContaminatedTransits'],
                    'bp_num_of_blended_transits': ['bpNumOfBlendedTransits'],
                    'solution_id': ['solutionId'],
                    'rp_coefficient_covariances': ['rpSpec', 'solution', 'covariance'],
                    'rp_coefficients': ['rpSpec', 'solution', 'parameters'],
                    'bp_coefficient_covariances': ['bpSpec', 'solution', 'covariance'],
                    'bp_coefficients': ['bpSpec', 'solution', 'parameters']}
