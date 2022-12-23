"""
error_correction.py
====================================
Module that implements the error correction over a multi-photometry.
"""

from functools import lru_cache
from math import isnan, floor
from os import path, listdir

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from tqdm import tqdm

from gaiaxpy.config.paths import config_path
from gaiaxpy.core.generic_functions import cast_output, _extract_systems_from_data, _warning
from gaiaxpy.core.generic_variables import pbar_colour, pbar_units
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.output.photometry_data import PhotometryData

correction_tables_path = path.join(config_path, 'correction_tables')


@lru_cache(maxsize=None)
def _get_correctable_systems():
    correction_files = listdir(correction_tables_path)
    systems = [filename.split('-')[2] for filename in correction_files]
    return systems


def _read_system_table(system):
    # Read system table
    try:
        correction_factors_path = path.join(correction_tables_path, f'DIDREQ-465-{system}-correction-factors.csv')
        correction_table = pd.read_csv(correction_factors_path, float_precision='round_trip')
        correction_table['bin_centre'] = (correction_table['min_Gmag_bin'] + correction_table['max_Gmag_bin']) / 2
    except FileNotFoundError:
        raise FileNotFoundError(f'No correction table found for system {system}.')
    return correction_table


def _get_correction_array(mag_G_values, system):
    # Read table here. We only want to read it once.
    correction_table = _read_system_table(system)
    correction_array = [_get_correction_factors(mag, correction_table) for mag in mag_G_values]
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
    factors = range_row[factor_columns]
    bin_centre = range_row['bin_centre']
    try:
        next_range_row = correction_table[correction_table['min_Gmag_bin'] == range_row['max_Gmag_bin']].iloc[0]
    except:
        return factors
    # Now for the rest
    if mag <= bin_centre:
        return factors
    # or interpolate
    elif bin_centre < mag < range_row['max_Gmag_bin']:
        next_factors = next_range_row[factor_columns]
        correction_factors = [interp1d(np.array([bin_centre, range_row['max_Gmag_bin']]),
                                       np.array([factor, next_factors[index]]))(mag) for index, factor in
                              enumerate(factors)]
        return np.array(correction_factors)
    else:
        raise ValueError('Check the variables being used. The program should never fall in this case.')


def _correct_system(system_df, correction_array):
    # Extract error columns
    error_df = system_df[[column for column in system_df.columns if '_error' in column]]
    rearranged_correction = [sublist for sublist in zip(*correction_array)]
    # Factors for each column
    for index, column in enumerate(error_df.columns):
        error_df[column] = error_df[column] * rearranged_correction[index]
    return error_df


# The correction can only be applied for the systems present in the config files
__correctable_systems = _get_correctable_systems()


def apply_error_correction(input_multi_photometry, photometric_system=None, output_path='.',
                           output_file='output_corrected_photometry', output_format=None, save_file=True):
    """
    Apply error correction (see Montegriffo et al., 2022, for more details). Infer photometric systems if not specified.

    Args:
        input_multi_photometry (DataFrame): Photometry DataFrame, can contain photometry for one or more systems.
        photometric_system (obj): Desired photometric system or list of photometric systems.
        output_path (str): Path where to save the output data.
        output_file (str): Name of the output file.
        output_format (str): Format to be used for the output file. If no format is given, then the output file will be
            in the same format as the input file.
        save_file (bool): Whether to save the output in a file. If false, output_format and output_file_name are
            ignored.

    Returns:
        DataFrame: A DataFrame of all synthetic photometry with corrected errors for the systems for which it is
            possible.
    """
    gaia_system = 'GaiaDr3Vega'
    gaia_G_mag_column = f'{gaia_system}_mag_G'
    input_multi_photometry, extension = InputReader(input_multi_photometry, apply_error_correction)._read()
    # Validate that it is a multi-photometry, but how? First try below:
    if not gaia_G_mag_column in input_multi_photometry.columns:
        raise ValueError('System Gaia_DR3_Vega, required to apply the error correction is not present in the input'
                         ' photometry.')
    columns = list(input_multi_photometry.columns)
    columns.remove('source_id')
    systems_in_data = _extract_systems_from_data(columns, photometric_system)
    # Only correct the systems that can be corrected
    systems = list(set(systems_in_data) & set(__correctable_systems))
    systems_to_skip = set(systems_in_data) - set(__correctable_systems)
    for system in systems_to_skip:
        _warning(f'System {system} does not have a correction table. The program will not apply error correction over'
                 f' this system.')
    # Now we have to apply the correction on each of the systems, but this correction depends on the G band
    for system in tqdm(systems, desc='Correcting systems', total=len(systems), unit=pbar_units['correction'],
                       leave=False, colour=pbar_colour):
        system_df = input_multi_photometry[[column for column in input_multi_photometry.columns if
                                            (column.startswith(system) and f'{system}Std' not in column) or
                                            column == gaia_G_mag_column]]
        # Get the correction factors for the mag G column
        correction_array = _get_correction_array(system_df[gaia_G_mag_column].values, system)
        # Correct error magnitudes
        corrected_system = _correct_system(system_df, correction_array)
        # Apply correction to the original input_multi_photometry
        input_multi_photometry.update(corrected_system)
    output_data = PhotometryData(input_multi_photometry)
    output_data.data = cast_output(output_data)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return input_multi_photometry
