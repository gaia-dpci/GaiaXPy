"""
error_correction.py
====================================
Module that implements the error correction over a multi-photometry.
"""

import numpy as np
import pandas as pd
from math import isnan, floor
from os import path, listdir
from gaiaxpy.config import config_path
from gaiaxpy.core import _extract_systems_from_data, _warning
from gaiaxpy.input_reader import InputReader
from gaiaxpy.output import PhotometryData
from scipy.interpolate import interp1d


correction_tables_path = path.join(config_path, 'correction_tables')

def _get_correctable_systems():
    correction_files = listdir(correction_tables_path)
    systems = [filename.split('-')[2] for filename in correction_files]
    return systems


def _get_correction_array(mag_G_values, system):
    # Read table here. We only want to read it once.
    correction_table = _read_system_table(system)
    correction_array = []
    for mag in mag_G_values:
        correction_factors = _get_correction_factors(mag, correction_table)
        correction_array.append(correction_factors)
    # One array per row in the original data
    return np.array(correction_array)


def _get_correction_factors(mag, correction_table):
    # Min and max range values in the table
    min_value = correction_table['min_Gmag_bin'].iloc[0]
    max_value = correction_table['max_Gmag_bin'].iloc[-1]
    # Factor columns
    factor_columns = [column for column in correction_table.columns if 'factor_' in column]
    # See whether the mag is in the table
    if mag > max_value or isnan(mag):
        return np.array(correction_table[factor_columns].iloc[-1])
    elif mag < min_value:
        return np.array(correction_table[factor_columns].iloc[0])
    # Else the mag is in the table
    min_mag = floor(mag)  # Find the range of the given mag
    # Extract the row of the table that matches this value
    range_row = correction_table[correction_table['min_Gmag_bin'] == min_mag].iloc[0]
    # If the column extracted is the last one, we have no way to extrapolate, so we keep the correction factors
    factors = range_row[factor_columns]; bin_centre = range_row['bin_centre']
    try:
        next_range_row = correction_table[correction_table['min_Gmag_bin'] == range_row['max_Gmag_bin']].iloc[0]
    except:
        return factors
    # Now for the rest
    if mag <= bin_centre:
        return factors
    # or interpolate
    elif bin_centre < mag and mag < range_row['max_Gmag_bin']:
        next_factors = next_range_row[factor_columns]
        correction_factors = []
        for index, factor in enumerate(factors):
            interpolator = interp1d(np.array([bin_centre, range_row['max_Gmag_bin']]),
                                    np.array([factor, next_factors[index]]))
            correction_factors.append(interpolator(mag))
        return np.array(correction_factors)
    else:
        raise ValueError('Check the variables being used. The program should never fall in this case.')


def _read_system_table(system):
    # Read system table
    try:
        correction_factors_path = path.join(correction_tables_path, f'DIDREQ-465-{system}-correction-factors.csv')
        correction_table = pd.read_csv(correction_factors_path, float_precision='round_trip')
        correction_table['bin_centre'] = (correction_table['min_Gmag_bin'] + correction_table['max_Gmag_bin']) / 2
    except FileNotFoundError:
        raise FileNotFoundError(f'No correction table found for system {system}.')
    return correction_table


def _correct_system(system_df, correction_array):
    # Extract error columns
    error_df = system_df[[column for column in system_df.columns if '_error' in column]]
    rearranged_correction = [sublist for sublist in zip(*correction_array)]
    # Factors for each column
    nrows = len(system_df)
    for index, column in enumerate(error_df.columns):
        correction_factors = rearranged_correction[index]
        error_df[column] = error_df[column] * correction_factors
    # Update system_df
    system_df.update(error_df)
    return system_df


def apply_error_correction(input_multi_photometry, photometric_system=None, output_path='.',
                           output_file='output_corrected_photometry', output_format=None, save_file=True):
    """
    Apply error correction. Infers photometric systems if not specified.

        output_path (str): Path where to save the output data.
    """
    gaia_system = 'GaiaDr3Vega'
    gaia_G_mag_column = f'{gaia_system}_mag_G'
    input_multi_photometry, extension = InputReader(input_multi_photometry, apply_error_correction)._read()
    # Validate that it is a multi-photometry, but how? First try below:
    if not gaia_G_mag_column in input_multi_photometry.columns:
        raise ValueError('System Gaia_DR3_Vega, necessary to apply the error correction is not present in the input photometry.')
    columns = list(input_multi_photometry.columns)
    columns.remove('source_id')
    systems_in_data = _extract_systems_from_data(columns, photometric_system)
    # The correction can only be applied for the systems present in the config files
    correctable_systems = _get_correctable_systems()
    # Only correct the systems that can be corrected
    systems = []
    for system in systems_in_data:
        if system in correctable_systems:
            systems.append(system)
        else:
            _warning(f'System {system} does not have a correction table. The program will not apply error correction over this system.')
    # Now we have to apply the correction on each of the systems, but this correction depends on the G band
    for system in systems:
        system_df = input_multi_photometry[[column for column in input_multi_photometry.columns if
                                            column.startswith(system) or column == gaia_G_mag_column]]
        # Get the correction factors for the mag G column
        correction_array = _get_correction_array(system_df[gaia_G_mag_column].values, system)
        # Correct error magnitudes
        corrected_system = _correct_system(system_df, correction_array)
        # Apply correction to the original input_multi_photometry
        input_multi_photometry.update(corrected_system)
    output_data = PhotometryData(input_multi_photometry)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return input_multi_photometry
