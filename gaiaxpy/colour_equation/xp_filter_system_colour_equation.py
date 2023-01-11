import math
from ast import literal_eval
from configparser import ConfigParser
from os import listdir
from os.path import join

import numpy as np
import pandas as pd
from numpy import poly1d
from tqdm import tqdm

from gaiaxpy.config.paths import filters_path
from gaiaxpy.core.generic_functions import cast_output, _validate_arguments
from gaiaxpy.core.generic_variables import pbar_colour, pbar_units
from gaiaxpy.generator.photometric_system import PhotometricSystem
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.output.photometry_data import PhotometryData

colour_eq_dir = join(filters_path, '..', 'colour_eq_files')


def _raise_key_error(key):
    raise KeyError(f'Required column {key} is not present in input data.')


def _compute_mag_error(data, band, system_label):
    return 2.5 * data[f'{system_label}_flux_error_{band}'] / (data[f'{system_label}_flux_{band}'] * math.log(10))


def _fill_systems_details(systems_to_correct):
    systems_details = dict()
    for system in systems_to_correct:
        label = system.get_system_label()
        systems_details[label] = dict()
        # Get bands and zero points
        systems_details[label]['bands_zp'] = dict(zip(system.get_bands(), system.get_zero_points()))
        # Load ini file
        config_parser = ConfigParser()
        config_parser.read(join(colour_eq_dir, f'{label}_colour_eq.ini'))
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


def _create_rows(single_system_df, system, colour_band_0, colour_band_1, systems_details):
    new_system_rows = [_generate_output_row(row, system, colour_band_0, colour_band_1, systems_details) for index, row
                       in tqdm(single_system_df.iterrows(), desc='Applying colour equation', total=len(single_system_df),
                               unit=pbar_units['colour_eq'], colour=pbar_colour, leave=False)]
    return pd.DataFrame(new_system_rows)


def _generate_output_df(input_synthetic_photometry, systems_details):
    synth_phot_df = input_synthetic_photometry.copy()
    column_names = synth_phot_df.columns
    # Extract columns corresponding to one system
    for label in systems_details.keys():
        filter_to_correct = systems_details[label]['filter']
        colour_band_0, colour_band_1 = _get_colour_bands(systems_details[label]['colour_index'])
        system_columns_with_colour = [column for column in column_names if column.startswith(f'{label}_') and
                                      column.endswith((f'_{filter_to_correct}', f'_{colour_band_0}',
                                                       f'_{colour_band_1}'))]
        single_system_df = synth_phot_df[system_columns_with_colour]
        corrected_system_df = _create_rows(single_system_df, label, colour_band_0, colour_band_1, systems_details)
        columns_to_correct = corrected_system_df.columns
        synth_phot_df[columns_to_correct] = corrected_system_df[columns_to_correct]
    return synth_phot_df


def _generate_output_row(row, system_label, colour_band_0, colour_band_1, systems_details):
    filter_to_correct = systems_details[system_label]['filter']
    mag = row[f'{system_label}_mag_{filter_to_correct}']
    mag_err = _compute_mag_error(row, filter_to_correct, system_label)
    mag_colour_0 = row[f'{system_label}_mag_{colour_band_0}']
    mag_colour_1 = row[f'{system_label}_mag_{colour_band_1}']
    colour = mag_colour_0 - mag_colour_1
    # Output corrected magnitude
    corrected_magnitude = mag + _get_correction(systems_details, colour, system_label)
    # Propagated colour error
    mag_err_1 = _compute_mag_error(row, colour_band_0, system_label)
    mag_err_2 = _compute_mag_error(row, colour_band_1, system_label)
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


def _get_available_colour_systems():
    """
    Get systems on which the colour equation can be applied.
    """
    return [filename.split('_')[0] for filename in colour_eq_dir]


def _get_colour_bands(colour_index):
    colour_band_0, colour_band_1 = colour_index.split('-')
    return colour_band_0, colour_band_1


def _set_colour_limit(colour, colour_range):
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


# Replaces 'contains'
def _is_in_range(colour, colour_range):
    return min(colour_range) <= colour <= max(colour_range)


def _get_correction(systems_details, colour, system_label):
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


def _get_systems_to_correct(systems) -> list:
    systems = [systems] if isinstance(systems, PhotometricSystem) else systems
    correctable_labels = [filename.split('_')[0] for filename in listdir(colour_eq_dir)]
    correctable_systems = [system for system in systems if system.get_system_label() in correctable_labels]
    return correctable_systems


def apply_colour_equation(input_synthetic_photometry, photometric_system=None, output_path='.',
                          output_file='corrected_photometry', output_format=None, save_file=True):
    """
    Apply the available colour correction to the input photometric system(s).
    
    Args:
        input_synthetic_photometry (DataFrame): Input photometry as returned by GaiaXPy generator.
        photometric_system (PhotometricSystem, list of PhotometricSystem): The photometric systems over which to apply
        the equations.
        output_path (str): The path of the output file.
        output_file (str): The name of the output file.
        output_format (str): The format of the output file (csv, fits, xml).
        save_file (bool): Whether to save the output file.
    
    Returns:
        DataFrame: The input photometry with colour equations applied if it corresponds.
    """
    function = apply_colour_equation  # Being able to extract the name of the current function would be ideal.
    _validate_arguments(function.__defaults__[2], output_file, save_file)
    input_synthetic_photometry, extension = InputReader(input_synthetic_photometry, function)._read()
    systems_to_correct = _get_systems_to_correct(photometric_system)
    systems_details = _fill_systems_details(systems_to_correct)
    output_df = _generate_output_df(input_synthetic_photometry, systems_details)
    output_data = PhotometryData(output_df)
    output_data.data = cast_output(output_data)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return output_df
