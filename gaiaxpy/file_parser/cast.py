"""
cast.py
====================================
Module to cast the data after parsing.
"""
import numpy as np
from numpy.ma import MaskError, getdata

# Fields of all formats including AVRO.
__type_map = {'source_id': 'int64', 'solution_id': 'int64', 'rp_n_parameters': 'int64', 'bp_n_parameters': 'int64',
              'rp_n_rejected_measurements': 'int64', 'bp_n_rejected_measurements': 'int64',
              'rp_n_measurements': 'int64', 'bp_n_measurements': 'int64',
              'rp_standard_deviation': 'float64', 'bp_standard_deviation': 'float64',
              'rp_num_of_transits': 'int64', 'bp_num_of_transits': 'int64',
              'rp_num_of_blended_transits': 'int64', 'bp_num_of_blended_transits': 'int64',
              'rp_num_of_contaminated_transits': 'int64', 'bp_num_of_contaminated_transits': 'int64',
              'rp_coefficients': 'O', 'bp_coefficients': 'O',
              'rp_coefficient_covariances': 'O', 'bp_coefficient_covariances': 'O',
              'rp_degrees_of_freedom': 'int64', 'bp_degrees_of_freedom': 'int64',
              'rp_n_relevant_bases': 'int64', 'bp_n_relevant_bases': 'int64',
              'rp_basis_function_id': 'int64', 'bp_basis_function_id': 'int64',
              'rp_chi_squared': 'float64', 'bp_chi_squared': 'float64',
              'rp_coefficient_errors': 'O', 'bp_coefficient_errors': 'O',
              'rp_coefficient_correlations': 'O', 'bp_coefficient_correlations': 'O',
              'rp_relative_shrinking': 'float64', 'bp_relative_shrinking': 'float64'}


def __replace_masked_constant(value):
    return float('NaN') if isinstance(value, np.ma.core.MaskedConstant) else value


def __replace_masked_array(value):
    if (isinstance(value, np.ma.core.MaskedArray) and getdata(value).size == 0) or (isinstance(value, float) and
                                                                                    value == 0.0):
        return np.array([])
    elif isinstance(value, np.ma.core.MaskedArray):
        return getdata(value)
    else:
        return value


def _cast(df):
    """
    Cast types to the defined ones to standardise the different input formats.

    Args:
        df (DataFrame): a DataFrame with parsed data from input files.
    """
    for column, type_value in __type_map.items():
        try:
            if type_value == 'O':
                df[column] = df[column].apply(lambda x: __replace_masked_array(x))
            else:
                df[column] = df[column].astype(type_value)
        except KeyError:
            continue  # Not every key is available in every case
        except ValueError as err:
            if np.isnan(np.sum(df[column].values)):
                pass  # There can be nan values, do nothing with them at this step
            else:
                print(f'Error casting input data: {err}')  # This is an actual error
        except MaskError:
            continue
    return df
