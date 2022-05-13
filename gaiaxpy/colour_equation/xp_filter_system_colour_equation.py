import ast
import math
import numpy as np
import pandas as pd
from configparser import ConfigParser
from os import listdir, path
from numpy import poly1d
from gaiaxpy.config import filters_path
from gaiaxpy.core import _extract_systems_from_data, _load_xpzeropoint_from_csv, \
                         _progress_tracker, _validate_arguments
from gaiaxpy.input_reader import InputReader
from gaiaxpy.output import PhotometryData


def _raise_key_error(key):
    raise KeyError(f'Required column {key} is not present in input data.')


def _compute_mag_error(data, band, system_label):
    return 2.5 * data[f'{system_label}_flux_error_{band}'] / (data[f'{system_label}_flux_{band}'] * math.log(10))


def _fill_systems_details(systems_to_correct):
    systems_details = {}
    if systems_to_correct:
        for system in systems_to_correct:
            systems_details[system] = {}
            # Get bands and zero points
            bands, zero_points = _load_xpzeropoint_from_csv(system)
            systems_details[system]['bands_zp'] = dict(zip(bands, zero_points))
            # Load ini file
            config_parser = ConfigParser()
            equation_file = path.join(filters_path, '..', 'colour_eq_files', f'{system}_colour_eq.ini')
            config_parser.read(equation_file)
            # The filter to be corrected (String)
            filter = config_parser.get(system, 'FILTER')
            systems_details[system]['filter'] = filter
            # The colour index (String)
            systems_details[system]['colour_index'] = config_parser.get(system, 'COLOUR_INDEX')
            # The colour equation (PolynomialFunction)
            # Reverse, coefficients were originally defined for the Java polyfunction
            coeffs = list(ast.literal_eval(config_parser.get(system, 'POLY_COEFFICIENTS')))[::-1]
            polyfunc = poly1d(coeffs)
            systems_details[system]['polyfunc'] = polyfunc
            # Derivative of the colour equation (UnivariateFunction)
            systems_details[system]['derivative'] = polyfunc.deriv()
            # Colour range for the correction (double[])
            colour_range = config_parser.get(system, 'COLOUR_RANGE')
            systems_details[system]['colour_range'] = ast.literal_eval(colour_range)
    return systems_details


def _create_rows(single_system_df, system, colour_band_0, colour_band_1, systems_details):
    new_system_rows = []
    nrows = len(single_system_df)

    @_progress_tracker
    def _execute_row(row, *args):
        system, colour_band_0, colour_band_1, systems_details = args[:4]
        new_row = _generate_output_row(row, system, colour_band_0, colour_band_1, systems_details)
        new_system_rows.append(new_row)
    for index, row in single_system_df.iterrows():
        _execute_row(row, system, colour_band_0, colour_band_1, systems_details, index, nrows)
    return pd.DataFrame(new_system_rows)


def _generate_output_df(input_synthetic_photometry, systems_in_data, systems_details):
    synt_phot_df = input_synthetic_photometry.copy()
    colour_equation_systems = _get_available_systems()
    # Intersection of systems in data and systems that can be corrected
    systems_to_correct = [system for system in systems_in_data if system in colour_equation_systems]
    if systems_to_correct:
        # Perform correction
        column_names = synt_phot_df.columns
        # Extract columns corresponding to one system
        for system in systems_to_correct:
            filter_to_correct = systems_details[system]['filter']
            colour_band_0, colour_band_1 = _get_colour_bands(systems_details[system]['colour_index'])
            system_columns_with_colour = [column for column in column_names if column.startswith(f'{system}_')
                              and column.endswith((f'_{filter_to_correct}', f'_{colour_band_0}', f'_{colour_band_1}'))]
            # Data to apply the colour equation
            single_system_df = synt_phot_df[system_columns_with_colour]
            new_system_df = _create_rows(single_system_df, system, colour_band_0, colour_band_1, systems_details)
            for column in new_system_df.columns:
                synt_phot_df[column] = new_system_df[column]
    return synt_phot_df


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
    colour_err = math.sqrt(mag_err_1**2 + mag_err_2**2)
    correction_err = colour_err * abs(systems_details[system_label]['derivative'](colour))
    # Total error on corrected magnitude
    out_err = math.sqrt(mag_err**2 + correction_err**2)
    new_row = {}
    new_row[f'{system_label}_mag_{filter_to_correct}'] = corrected_magnitude
    zp = systems_details[system_label]['bands_zp'][filter_to_correct]
    out_flux = 10**(-0.4 * (corrected_magnitude - zp))
    out_flux_err = out_err * out_flux * math.log(10) / 2.5
    new_row[f'{system_label}_flux_{filter_to_correct}'] = out_flux
    new_row[f'{system_label}_flux_error_{filter_to_correct}'] = out_flux_err
    return new_row


def _get_available_systems():
    """
    Get systems on which the colour equation can be applied.
    """
    return [filename.split('_')[0] for filename in listdir(path.join(filters_path, '..', 'colour_eq_files'))]


def _get_colour_bands(colour_index):
    colour_band_0, colour_band_1 = colour_index.split('-')
    return colour_band_0, colour_band_1


def _set_colour_limit(colour, colour_range):
    if colour < min(colour_range):
        colour_limit = min(colour_range)
    elif colour > max(colour_range):
        colour_limit = max(colour_range)
    else:
        raise ValueError('The condition for one of the previous statements must be True. Error in colour or colour_range.')
    return colour_limit


def _generate_polynomial(colour, colour_limit, system_polyfunc):
    v = system_polyfunc(colour_limit)
    m = system_polyfunc.deriv()(colour_limit)
    return v + m * (colour - colour_limit)


# Replaces 'contains'
def _is_in_range(colour, colour_range):
    return min(colour_range) <= colour and colour <= max(colour_range)


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


def apply_colour_equation(input_synthetic_photometry, photometric_system=None, output_path='.',
                          output_file='corrected_photometry', output_format=None, save_file=True):
    """
    Apply the available colour correction to the input photometric system(s).

    Args:
        input_synthetic_photometry (DataFrame): Input photometry as returned by GaiaXPy's generator.
        photometric_system (PhotometricSystem, list of PhotometricSystem): The photometric systems over which to apply the equations.
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
    systems_in_data = _extract_systems_from_data(input_synthetic_photometry.columns, photometric_system)
    colour_equation_systems = _get_available_systems()
    # Intersection of systems in data and systems that can be corrected
    systems_to_correct = [system for system in systems_in_data if system in colour_equation_systems]
    # Only extract the data of the systems that need to be corrected
    systems_details = _fill_systems_details(systems_to_correct)
    output_df = _generate_output_df(input_synthetic_photometry, systems_in_data, systems_details)
    output_data = PhotometryData(output_df)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return output_df
