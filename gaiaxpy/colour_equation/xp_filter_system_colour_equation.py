"""
xp_filter_system_colour_equation.py
====================================
Module that implements the colour equation functionality.
"""

import math
from ast import literal_eval
from configparser import ConfigParser
from os import listdir
from pathlib import Path
from typing import Union, Optional

import numpy as np
import pandas as pd
from numpy import poly1d
from tqdm import tqdm

from gaiaxpy.config.paths import filters_path
from gaiaxpy.core.generic_functions import cast_output, validate_arguments
from gaiaxpy.core.generic_variables import pbar_colour, pbar_units
from gaiaxpy.generator.photometric_system import PhotometricSystem
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.output.photometry_data import PhotometryData

colour_eq_dir = Path(filters_path, '..', 'colour_eq_files')


def __raise_key_error(key):
    """
    Raise a KeyError with a specific error message.

    Args:
        key (str): The missing key that triggered the error.

    Raises:
        KeyError: A KeyError with a specific error message indicating the missing key.
    """
    raise KeyError(f'Required column {key} is not present in input data.')


def __compute_mag_error(data, band, system_label):
    """
    Compute magnitude error based on flux error.

    Args:
        data (dict): A dictionary containing the input data.
        band (str): The band to use.
        system_label (str): The system being used.

    Returns:
        float: The magnitude error.
    """
    return 2.5 * data[f'{system_label}_flux_error_{band}'] / (data[f'{system_label}_flux_{band}'] * math.log(10))


def __fill_systems_details(systems_to_correct):
    """
    Get the details of the systems that will be corrected.

    Args:
        systems_to_correct (list): A list containing the systems to be corrected.

    Returns:
        dict: A dictionary containing the details of the given systems.
    """
    systems_details = dict()
    for system in systems_to_correct:
        label = system.get_system_label()
        systems_details[label] = dict()
        # Get bands and zero points
        systems_details[label]['bands_zp'] = dict(zip(system.get_bands(), system.get_zero_points()))
        # Load ini file
        config_parser = ConfigParser()
        config_parser.read(Path(colour_eq_dir, f'{label}_colour_eq.ini'))
        systems_details[label]['filter'] = config_parser.get(label, 'FILTER')  # The filter to be corrected (string)
        systems_details[label]['colour_index'] = config_parser.get(label, 'COLOUR_INDEX')  # The colour index (string)
        # The colour equation (PolynomialFunction)
        # Reverse, coefficients were originally defined for the Java polyfunction
        coefficients = list(literal_eval(config_parser.get(label, 'POLY_COEFFICIENTS')))[::-1]
        polyfunc = poly1d(coefficients)
        systems_details[label]['polyfunc'] = polyfunc
        systems_details[label]['derivative'] = polyfunc.deriv()  # Colour equation derivative (UnivariateFunction)
        colour_range = config_parser.get(label, 'COLOUR_RANGE')  # Colour range for the correction (double[])
        systems_details[label]['colour_range'] = literal_eval(colour_range)
    return systems_details


def __create_rows(single_system_df, system, colour_band_0, colour_band_1, systems_details):
    """
    Create output rows for a systems.
    """
    new_system_rows = [__generate_output_row(row, system, colour_band_0, colour_band_1, systems_details) for row in
                       single_system_df.to_dict('records')]
    return pd.DataFrame(new_system_rows)


def _generate_output_df(input_synthetic_photometry, systems_details, disable_info=False):
    synth_phot_df = input_synthetic_photometry.copy()
    column_names = synth_phot_df.columns
    # Extract columns corresponding to one system
    system_keys = systems_details.keys()
    for label in tqdm(system_keys, desc='Applying colour equation', total=len(system_keys),
                      unit=pbar_units['colour_eq'], colour=pbar_colour, leave=False, disable=disable_info):
        filter_to_correct = systems_details[label]['filter']
        colour_band_0, colour_band_1 = _get_colour_bands(systems_details[label]['colour_index'])
        system_columns_with_colour = [column for column in column_names if column.startswith(f'{label}_') and
                                      column.endswith((f'_{filter_to_correct}', f'_{colour_band_0}',
                                                       f'_{colour_band_1}'))]
        single_system_df = synth_phot_df[system_columns_with_colour]
        corrected_system_df = __create_rows(single_system_df, label, colour_band_0, colour_band_1, systems_details)
        columns_to_correct = corrected_system_df.columns
        synth_phot_df[columns_to_correct] = corrected_system_df[columns_to_correct]
    return synth_phot_df


def __generate_output_row(row, system_label, colour_band_0, colour_band_1, systems_details):
    filter_to_correct = systems_details[system_label]['filter']
    mag = row[f'{system_label}_mag_{filter_to_correct}']
    mag_err = __compute_mag_error(row, filter_to_correct, system_label)
    mag_colour_0 = row[f'{system_label}_mag_{colour_band_0}']
    mag_colour_1 = row[f'{system_label}_mag_{colour_band_1}']
    colour = mag_colour_0 - mag_colour_1
    # Output corrected magnitude
    corrected_magnitude = mag + _get_correction(systems_details, colour, system_label)
    # Propagated colour error
    mag_err_1 = __compute_mag_error(row, colour_band_0, system_label)
    mag_err_2 = __compute_mag_error(row, colour_band_1, system_label)
    colour_err = math.sqrt(mag_err_1 ** 2 + mag_err_2 ** 2)
    correction_err = colour_err * abs(systems_details[system_label]['derivative'](colour))
    # Total error on corrected magnitude
    out_err = math.sqrt(mag_err ** 2 + correction_err ** 2)
    new_row = dict()
    new_row[f'{system_label}_mag_{filter_to_correct}'] = corrected_magnitude
    zp = systems_details[system_label]['bands_zp'][filter_to_correct]
    out_flux = 10 ** (-0.4 * (corrected_magnitude - zp))
    out_flux_err = out_err * out_flux * math.log(10) / 2.5
    new_row[f'{system_label}_flux_{filter_to_correct}'] = out_flux
    new_row[f'{system_label}_flux_error_{filter_to_correct}'] = out_flux_err
    return new_row


def _get_colour_bands(colour_index):
    """
    Split the bands of a colour index.

    Args:
        colour_index (str): Colour index containing two bands separated by a hyphen (e.g. U-V).

    Returns:
        tuple: Tuple of two elements containing the bands for the colour index as strings.
    """
    colour_band_0, colour_band_1 = colour_index.split('-')
    return colour_band_0, colour_band_1


def _set_colour_limit(colour, colour_range):
    """
    Set the colour limit to either the minimum or maximum value in the given colour range.

    Args:
        colour (float): The colour value.
        colour_range (list): A list of two values representing the minimum and maximum allowed values for the colour.

    Returns:
        float: The minimum or maximum value in the colour range, whichever is closest to the input `colour` value.

    Raises:
        ValueError: If the input `colour` value is not within the specified `colour_range`.
    """
    if colour < min(colour_range):
        colour_limit = min(colour_range)
    elif colour > max(colour_range):
        colour_limit = max(colour_range)
    else:
        raise ValueError(
            'The condition for one of the previous statements must be True. Error in colour or colour_range.')
    return colour_limit


def _generate_polynomial(colour, colour_limit, system_polyfunc):
    v = system_polyfunc(colour_limit)
    m = system_polyfunc.deriv()(colour_limit)
    return v + m * (colour - colour_limit)


# Replaces Java 'contains'
def _is_in_range(colour: float, colour_range: list):
    return min(colour_range) <= colour <= max(colour_range)


def _get_correction(systems_details: dict, colour: float, system_label: str):
    colour_range = systems_details[system_label]['colour_range']
    polyfunc = systems_details[system_label]['polyfunc']
    # Check whether colour is nan
    if math.isnan(colour):
        return np.nan
    # Check if in range after being sure that colour is not nan
    in_range = _is_in_range(colour, colour_range)
    if in_range:
        return polyfunc(colour)
    elif not in_range:
        colour_limit = _set_colour_limit(colour, colour_range)
        return _generate_polynomial(colour, colour_limit, polyfunc)
    else:
        raise ValueError('At least one variable does not comply with any of the previous statements.')


def __get_systems_to_correct(systems: Union[list, PhotometricSystem]) -> list:
    systems = [systems] if isinstance(systems, PhotometricSystem) else systems
    correctable_labels = [filename.split('_')[0] for filename in listdir(colour_eq_dir)]
    correctable_systems = [system for system in systems if system.get_system_label() in correctable_labels]
    return correctable_systems


def apply_colour_equation(input_synthetic_photometry: pd.DataFrame,
                          photometric_system: Union[list, PhotometricSystem] = None, output_path: str = '.',
                          output_file: str = 'corrected_photometry', output_format: Optional[str] = None,
                          save_file: bool = True):
    """
    Apply the available colour correction to the input photometric system(s).

    Args:
        input_synthetic_photometry (DataFrame): Input photometry as returned by GaiaXPy generator.
        photometric_system (PhotometricSystem, list of PhotometricSystem): The photometric systems over which to apply
        the equations.
        output_path (str): The path of the output file.
        output_file (str): Name of the output file without extension (e.g. 'my_file').
        output_format (str): Desired output format. If no format is given, the output file format will be the same as
            the input file (e.g. 'csv').
        save_file (bool): Whether to save the output file.

    Returns:
        DataFrame: The input photometry with colour equations applied if it corresponds.
    """
    return _apply_colour_equation(input_synthetic_photometry=input_synthetic_photometry,
                                  photometric_system=photometric_system, output_path=output_path,
                                  output_file=output_file, output_format=output_format, save_file=save_file)


def _apply_colour_equation(input_synthetic_photometry: pd.DataFrame,
                           photometric_system: Union[list, PhotometricSystem] = None, output_path: str = '.',
                           output_file: str = 'corrected_photometry', output_format: Optional[str] = None,
                           save_file: bool = True, disable_info=False):
    function = apply_colour_equation
    validate_arguments(function.__defaults__[2], output_file, save_file)
    input_synthetic_photometry, extension = InputReader(input_synthetic_photometry, function,
                                                        disable_info=disable_info).read()
    systems_to_correct = __get_systems_to_correct(photometric_system)
    systems_details = __fill_systems_details(systems_to_correct)
    output_df = _generate_output_df(input_synthetic_photometry, systems_details, disable_info=disable_info)
    output_data = PhotometryData(output_df)
    output_data.data = cast_output(output_data)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return output_data.data
