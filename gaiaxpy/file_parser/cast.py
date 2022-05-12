"""
cast.py
====================================
Module to cast the data after parsing.
"""
import numpy as np
from numpy import dtype
from numpy.ma import MaskError

# Fields of the AVRO file and other formats.
type_map = {'source_id': dtype('int64'),
            'solution_id': dtype('int64'),
            'rp_n_parameters': dtype('int64'),
            'bp_n_parameters': dtype('int64'),
            'rp_n_rejected_measurements': dtype('int64'),
            'bp_n_rejected_measurements': dtype('int64'),
            'rp_n_measurements': dtype('int64'),
            'bp_n_measurements': dtype('int64'),
            'rp_standard_deviation': dtype('float64'),
            'bp_standard_deviation': dtype('float64'),
            'rp_num_of_transits': dtype('int64'),
            'bp_num_of_transits': dtype('int64'),
            'rp_num_of_blended_transits': dtype('int64'),
            'bp_num_of_blended_transits': dtype('int64'),
            'rp_num_of_contaminated_transits': dtype('int64'),
            'bp_num_of_contaminated_transits': dtype('int64'),
            'rp_coefficients': dtype('O'),
            'bp_coefficients': dtype('O'),
            'rp_coefficient_covariances': dtype('O'),
            'bp_coefficient_covariances': dtype('O'),
            'rp_degrees_of_freedom': dtype('int64'),
            'bp_degrees_of_freedom': dtype('int64'),
            'rp_n_relevant_bases': dtype('int64'),
            'bp_n_relevant_bases': dtype('int64'),
            'rp_basis_function_id': dtype('int64'),
            'bp_basis_function_id': dtype('int64'),
            'rp_chi_squared': dtype('float64'),
            'bp_chi_squared': dtype('float64'),
            'rp_coefficient_errors': dtype('O'),
            'bp_coefficient_errors': dtype('O'),
            'rp_coefficient_correlations': dtype('O'),
            'bp_coefficient_correlations': dtype('O'),
            'rp_relative_shrinking': dtype('float64'),
            'bp_relative_shrinking': dtype('float64')}


def _cast(df):
    """
    Cast types to the defined ones to standardise the different input formats.

    Args:
        df (DataFrame): a DataFrame with parsed data from input files.
    """
    for column in df.columns:
        try:
            df[column] = df[column].astype(type_map[column])
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
