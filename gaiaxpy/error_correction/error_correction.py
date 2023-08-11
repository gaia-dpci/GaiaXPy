"""
error_correction.py
====================================
Module that implements the error correction over a multi-photometry.
"""

from functools import lru_cache
from os import listdir
from os.path import join

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from tqdm import tqdm

from gaiaxpy.config.paths import correction_tables_path
from gaiaxpy.core.generic_functions import cast_output, _extract_systems_from_data, _warning
from gaiaxpy.core.generic_variables import pbar_colour, pbar_units
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.output.photometry_data import PhotometryData


@lru_cache(maxsize=None)
def _get_correctable_systems():
    correction_files = listdir(correction_tables_path)
    systems = [filename.split('-')[2] for filename in correction_files]
    return systems


def _read_system_table(system):
    try:
        correction_factors_path = join(correction_tables_path, f'DIDREQ-465-{system}-correction-factors.csv')
        correction_table = pd.read_csv(correction_factors_path, float_precision='high')
    except FileNotFoundError:
        raise FileNotFoundError(f'No correction table found for system {system}.')
    correction_table['bin_centre'] = (correction_table['min_Gmag_bin'] + correction_table['max_Gmag_bin']) / 2
    return correction_table


def _get_correction_array(_mag_G_values, system):
    correction_table = _read_system_table(system)
    min_value, max_value = correction_table['min_Gmag_bin'].iloc[0], correction_table['max_Gmag_bin'].iloc[-1]
    floor_mag_dict = correction_table.set_index('min_Gmag_bin').T.to_dict()
    factor_columns = [col for col in correction_table.columns if 'factor_' in col]
    _mag_G_values = _mag_G_values.to_frame(name='mag_G')
    _mag_G_values['row'] = _mag_G_values['mag_G'].map(lambda x: floor_mag_dict.get(float(np.floor(x))))
    return _mag_G_values.apply(_get_correction_factor, args=(correction_table, factor_columns,
                                                             min_value, max_value,), axis=1)


def _get_correction_factor(mag_row, correction_table, factor_columns, min_value, max_value):
    mag = mag_row['mag_G']
    row = mag_row['row']
    if (mag > max_value) or pd.isna(mag):
        return correction_table[factor_columns].iloc[-1].values
    elif mag < min_value:
        return correction_table[factor_columns].iloc[0].values
    bin_centre = row['bin_centre']
    factors = np.array([row[factor] for factor in factor_columns])
    if mag <= bin_centre:
        return factors
    range_row_max_Gmag_bin = row['max_Gmag_bin']
    if bin_centre < mag < range_row_max_Gmag_bin:
        try:
            next_range_row = correction_table[correction_table['min_Gmag_bin'] == range_row_max_Gmag_bin].iloc[0]
            next_factors = next_range_row[factor_columns]
        except IndexError:
            return factors
        return interp1d(np.array([bin_centre, range_row_max_Gmag_bin]), np.vstack([factors, next_factors]), axis=0)(mag)
    # Raise an exception if none of the conditions match
    raise ValueError('Check the variables being used. The program should never fall in this case.')


def _correct_system(system_df, correction_array):
    # Extract error columns
    error_df = system_df[[column for column in system_df.columns if '_error' in column]]
    error_df_columns = error_df.columns
    if len(error_df_columns) != len(correction_array[0]):
        raise ValueError('DataFrames should have the same number of columns.')
    error_df = np.array(error_df)
    correction_array = np.array([x for x in correction_array])
    product_array = error_df * correction_array
    return pd.DataFrame(product_array, columns=error_df_columns)


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
        output_file (str): Name of the output file without extension (e.g. 'my_file').
        output_format (str): Desired output format. If no format is given, the output file format will be the same as
            the input file (e.g. 'csv').
        save_file (bool): Whether to save the output in a file. If false, output_format and output_file_name are
            ignored.

    Returns:
        DataFrame: A DataFrame of all synthetic photometry with corrected errors for the systems for which it is
            possible.
    """
    return _apply_error_correction(input_multi_photometry, photometric_system=photometric_system,
                                   output_path=output_path, output_file=output_file, output_format=output_format,
                                   save_file=save_file)


def _apply_error_correction(input_multi_photometry, photometric_system=None, output_path='.',
                            output_file='output_corrected_photometry', output_format=None, save_file=True,
                            disable_info=False):
    gaia_system = 'GaiaDr3Vega'
    gaia_G_mag_column = f'{gaia_system}_mag_G'
    input_multi_photometry, extension = InputReader(input_multi_photometry, apply_error_correction,
                                                    disable_info=disable_info).read()
    # Validate that it is a multi-photometry, but how? First try below:
    if gaia_G_mag_column not in input_multi_photometry.columns:
        raise ValueError('System Gaia_DR3_Vega, required to apply the error correction is not present in the input'
                         ' photometry.')
    columns = list(input_multi_photometry.columns)
    columns.remove('source_id')
    systems_in_data = _extract_systems_from_data(columns, photometric_system)
    # Only correct the systems that can be corrected
    systems = list(set(systems_in_data) & set(__correctable_systems))
    systems_to_skip = set(systems_in_data) - set(__correctable_systems)
    if systems_to_skip and not disable_info:
        print()
    for system in systems_to_skip:
        _warning(f'System {system} does not have a correction table. The program will not apply error correction over'
                 ' this system.')
    for system in tqdm(systems, desc='Correcting systems', total=len(systems), unit=pbar_units['correction'],
                       leave=False, colour=pbar_colour):
        system_df = input_multi_photometry[[column for column in input_multi_photometry.columns if
                                            (column.startswith(system) and f'{system}Std' not in column) or
                                            column == gaia_G_mag_column]]
        # Get the correction factors for the mag G column
        correction_array = _get_correction_array(system_df[gaia_G_mag_column], system)
        # Correct error magnitudes
        corrected_system = _correct_system(system_df, correction_array)
        # Apply correction to the original input_multi_photometry
        input_multi_photometry.update(corrected_system)
    output_data = PhotometryData(input_multi_photometry)
    output_data.data = cast_output(output_data)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return input_multi_photometry
