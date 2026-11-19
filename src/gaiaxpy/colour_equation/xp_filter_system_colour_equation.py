"""Apply DR3 passband corrections expressed as polynomials of a system's colour.

The selected equation supplies the target passband, two-band colour, polynomial
and colour limits. Recalculate the target magnitude, flux and flux error while
preserving the other photometry fields.
"""

import math
from ast import literal_eval
from os import listdir
from pathlib import Path
from sys import stdout
from typing import Union, Optional

import numpy as np
import yaml
from numpy import poly1d
from tqdm import tqdm

from gaiaxpy.config.paths import colour_equation_dir
from gaiaxpy.core.generic_functions import cast_output, mag_to_flux
from gaiaxpy.core.generic_variables import RELEASES, pbar_colour, pbar_units, pbar_message
from gaiaxpy.core.input_validator import validate_save_arguments, validate_overwrite
from gaiaxpy.input_reader.dataframe_reader import DataFrameReader
from gaiaxpy.output.photometry_data import PhotometryData
from gaiaxpy.photometric_system.photometric_system import PhotometricSystem


def _get_colour_equation_file(label):
    """Return the configured directory's <label>_colour_eq.yaml path.
    """
    return Path(colour_equation_dir, f'{label}_colour_eq.yaml')


def __compute_mag_error(data: dict, band: str, system_label: str) -> float:
    """Convert a passband's flux error to a magnitude error.

    Args:
        data (dict): Source photometry keyed by full column name.
        band (str): Passband name, preserving its configured case.
        system_label (str): Full column label, such as 'DR3_JkcStd'.

    Returns:
        float: The magnitude error: 2.5 * flux_error / (flux * ln(10)).

    Notes:
        No absolute value or special handling of zero flux is applied. Missing
        fields raise KeyError; zero flux can raise ZeroDivisionError.
    """
    return 2.5 * data[f'{system_label}_flux_error_{band}'] / (data[f'{system_label}_flux_{band}'] * math.log(10))


def __fill_systems_details(systems_to_correct: list) -> dict:
    """Load each selected system's colour equation and passband zero points.

    Args:
        systems_to_correct (list): Supported photometric-system members.

    Returns:
        dict: Full system labels mapped to bands_zp, filter, colour_index,
        polyfunc, derivative and colour_range. Zero points come from the selected
        filter; the remaining values come from its bundled colour-equation YAML.

    Notes:
        POLY_COEFFICIENTS is stored as text in ascending power order. Reverse
        its values when constructing NumPy's poly1d, which expects descending
        power order. File-reading, YAML-parsing and invalid configuration-field
        errors are reported to the caller.
    """
    systems_details = dict()
    for system in systems_to_correct:
        label = f'{system.value.get_system_prefix()}_{system.get_system_label()}'
        systems_details[label] = dict()
        # Get bands and zero points
        systems_details[label]['bands_zp'] = dict(zip(system.get_bands(), system.get_zero_points()))
        with open(_get_colour_equation_file(label)) as f:
            config_parser = yaml.safe_load(f)
        systems_details[label]['filter'] = config_parser.get(label).get('FILTER')  # The filter to be corrected (str)
        systems_details[label]['colour_index'] = config_parser.get(label).get('COLOUR_INDEX')  # The colour index (str)
        coefficients = np.array(literal_eval(config_parser.get(label).get('POLY_COEFFICIENTS')))[::-1]
        polyfunc = poly1d(coefficients)
        systems_details[label]['polyfunc'] = polyfunc
        systems_details[label]['derivative'] = polyfunc.deriv()  # Colour equation derivative (UnivariateFunction)
        colour_range = config_parser.get(label).get('COLOUR_RANGE')  # Colour range for the correction (double[])
        systems_details[label]['colour_range'] = colour_range
    return systems_details


def __generate_output_row(row: dict, system_label: str, colour_band_0: str, colour_band_1: str, systems_details: dict) \
        -> dict:
    """Create a dictionary containing the corrected values for an output row corresponding to a system.

    Args:
        row (dict): Magnitude, flux and flux-error fields for the target and
            both colour passbands.
        system_label (str): Full system column label.
        colour_band_0 (str): First colour passband.
        colour_band_1 (str): Second colour passband. Colour is the first
            magnitude minus the second.
        systems_details (dict): Loaded colour equations keyed by system label.

    Returns:
        dict: Three replacement values: target magnitude, flux and flux error.
        Add the colour correction to the input magnitude, then convert back
        to flux using the target passband's zero point.
    """
    filter_to_correct = systems_details[system_label]['filter']
    mag = row[f'{system_label}_mag_{filter_to_correct}']
    mag_err = __compute_mag_error(row, filter_to_correct, system_label)
    mag_colour_0 = row[f'{system_label}_mag_{colour_band_0}']
    mag_colour_1 = row[f'{system_label}_mag_{colour_band_1}']
    colour = mag_colour_0 - mag_colour_1
    # Output corrected magnitude
    corrected_magnitude = mag + __get_correction(systems_details, colour, system_label)
    # Propagated colour error
    mag_err_1 = __compute_mag_error(row, colour_band_0, system_label)
    mag_err_2 = __compute_mag_error(row, colour_band_1, system_label)
    colour_err = math.sqrt(mag_err_1 ** 2 + mag_err_2 ** 2)
    correction_err = colour_err * abs(systems_details[system_label]['derivative'](colour))
    # Total error on corrected magnitude
    out_err = math.sqrt(mag_err ** 2 + correction_err ** 2)
    corrected_row = dict()
    corrected_row[f'{system_label}_mag_{filter_to_correct}'] = corrected_magnitude
    zp = systems_details[system_label]['bands_zp'][filter_to_correct]
    out_flux = mag_to_flux(corrected_magnitude, zp)
    out_flux_err = out_err * out_flux * math.log(10) / 2.5
    corrected_row[f'{system_label}_flux_{filter_to_correct}'] = out_flux
    corrected_row[f'{system_label}_flux_error_{filter_to_correct}'] = out_flux_err
    return corrected_row


def __create_rows(single_system_df: 'pd.DataFrame', system: str, colour_band_0: str, colour_band_1: str,
                  systems_details: dict) -> 'pd.DataFrame':
    """Create the corrected output for a system.

    Args:
        single_system_df (pandas.DataFrame): Target and colour-passband
            magnitudes, fluxes and flux errors.
        system (str): Full system column label.
        colour_band_0 (str): First colour passband.
        colour_band_1 (str): Second colour passband.
        systems_details (dict): Loaded equation configuration by system label.

    Returns:
        pandas.DataFrame: Corrected target magnitude, flux and flux-error
        columns in input row order, with a new default integer index.
    """
    new_system_rows = [__generate_output_row(row, system, colour_band_0, colour_band_1, systems_details) for row in
                       single_system_df.to_dict('records')]

    from pandas import DataFrame as pdDf
    return pdDf(new_system_rows)


def __generate_output_df(input_synthetic_photometry: 'pd.DataFrame', systems_details: dict,
                         disable_info: bool = False) -> 'pd.DataFrame':
    """Replace the corrected passbands in a copy of the photometry table.

    Args:
        input_synthetic_photometry (pandas.DataFrame): Prepared photometry with
            a default integer index, matching the replacement rows' index.
        systems_details (dict): Loaded equations keyed by full system label.
        disable_info (bool): Suppress the per-system progress bar.

    Returns:
        pandas.DataFrame: Copy with each configured target's magnitude, flux
        and flux error replaced. Other columns are unchanged. An empty equation
        mapping returns a copy without applying corrections.
    """
    __FUNCTION_KEY = 'colour_eq'
    synth_phot_df = input_synthetic_photometry.copy()
    column_names = synth_phot_df.columns
    # Extract columns corresponding to one system
    system_keys = systems_details.keys()
    for label in tqdm(system_keys, desc=pbar_message[__FUNCTION_KEY], total=len(system_keys),
                      unit=pbar_units[__FUNCTION_KEY], colour=pbar_colour, leave=False, disable=disable_info,
                      file=stdout):
        filter_to_correct = systems_details[label]['filter']
        colour_band_0, colour_band_1 = __get_colour_bands(systems_details[label]['colour_index'])
        system_columns_with_colour = [column for column in column_names if column.startswith(f'{label}_') and
                                      column.endswith((f'_{filter_to_correct}', f'_{colour_band_0}',
                                                       f'_{colour_band_1}'))]
        single_system_df = synth_phot_df[system_columns_with_colour]
        corrected_system_df = __create_rows(single_system_df, label, colour_band_0, colour_band_1, systems_details)
        columns_to_correct = corrected_system_df.columns
        synth_phot_df[columns_to_correct] = corrected_system_df[columns_to_correct]
    return synth_phot_df


def __get_colour_bands(colour_index: str) -> tuple[str, str]:
    """Split a colour index into the first and second passband names.

    Args:
        colour_index (str): Exactly two names separated by a hyphen, such as
            'B-V' or 'g-i'. Their order defines the magnitude subtraction.

    Returns:
        tuple[str, str]: First and second passband names.

    Raises:
        ValueError: Splitting does not produce exactly two names.
    """
    colour_band_0, colour_band_1 = colour_index.split('-')
    return colour_band_0, colour_band_1


def __set_colour_limit(colour: float, colour_range: list) -> float:
    """Set the colour limit to either the minimum or maximum value in the given colour range.

    Args:
        colour (float): The colour value.
        colour_range (list): Range limits; their minimum and maximum are used.

    Returns:
        float: The minimum or maximum value in the colour range, whichever is closest to the
        input `colour` value.

    Raises:
        ValueError: colour is not strictly below or above the range.
    """
    if colour < min(colour_range):
        colour_limit = min(colour_range)
    elif colour > max(colour_range):
        colour_limit = max(colour_range)
    else:
        raise ValueError(
            'The condition for one of the previous statements must be True. Error in colour or colour_range.')
    return colour_limit


def __extrapolate_correction(colour: float, colour_limit: float,
                             system_polyfunc: np.poly1d) -> float:
    """Compute the correction outside the colour range by linear extrapolation.

    Use the polynomial's value and first derivative at the nearest boundary.

    Args:
        colour (float): Colour at which to compute the correction.
        colour_limit (float): Nearest configured range boundary.
        system_polyfunc (numpy.poly1d): Colour-correction polynomial.

    Returns:
        float: P(colour_limit) + P'(colour_limit) * (colour - colour_limit).
    """
    v = system_polyfunc(colour_limit)
    m = system_polyfunc.deriv()(colour_limit)
    return v + m * (colour - colour_limit)


def __is_in_range(colour: float, colour_range: list) -> bool:
    """Return whether the colour lies between the minimum and maximum limits, inclusively."""
    return min(colour_range) <= colour <= max(colour_range)


def __get_correction(systems_details: dict, colour: float, system_label: str) -> float:
    """Compute the correction to add to the selected system's target magnitude.

    Use the configured polynomial within the colour range, including its
    boundaries. Outside the range, extrapolate linearly using the polynomial's
    value and first derivative at the nearest boundary.

    Args:
        systems_details (dict): Colour-equation configurations keyed by system label.
        colour (float): First minus second magnitude in the configured colour index.
        system_label (str): Label identifying the system's colour equation.

    Returns:
        float: Additive magnitude correction, or NaN if colour is NaN.
    """
    colour_range = systems_details[system_label]['colour_range']
    polyfunc = systems_details[system_label]['polyfunc']
    # Check whether colour is nan
    if math.isnan(colour):
        return np.nan
    # Check if in range after being sure that colour is not nan
    in_range = __is_in_range(colour, colour_range)
    if in_range:
        return polyfunc(colour)
    elif not in_range:
        colour_limit = __set_colour_limit(colour, colour_range)
        return __extrapolate_correction(colour, colour_limit, polyfunc)
    else:
        raise ValueError('At least one variable does not comply with any of the previous statements.')


def __get_systems_to_correct(systems: Union[list, 'PhotometricSystem']) -> list:
    """Select explicitly requested DR3 systems with matching bundled equation labels.

    Args:
        systems (PhotometricSystem or list): Current PhotometricSystem member or list
            of PhotometricSystem members.
            An explicit selection is required; None is not inferred from data.

    Returns:
        list: Selected DR3 PhotometricSystem members whose full column labels
        appear in colour equation discovery, in selection order.

    Notes:
        Matching uses the complete column label. Additional systems do not
        inherit a built-in equation merely by sharing its base name.
    """
    systems = [systems] if isinstance(systems, PhotometricSystem) else systems
    # These colour equations were derived for DR3; filenames alone must not enable their application to another release.
    systems = [system for system in systems if system.value.release == RELEASES.dr3]
    if not systems:
        return []
    correctable_labels = get_colour_correctable_system_labels()
    correctable_systems = [system for system in systems if
                           f'{system.value.get_system_prefix()}_{system.get_system_label()}' in correctable_labels]
    return correctable_systems


def get_colour_correctable_system_labels() -> list[str]:
    """Extract system labels from filenames in the configured DR3 equation directory.

    Returns:
        list[str]: Each filename's first two underscore-separated parts joined
        by an underscore, such as 'DR3_JkcStd'. Directory order is retained.

    Notes:
        This lists filenames without opening or validating their contents.
        Equation selection separately checks that requested systems belong to DR3.
    """
    correctable_labels = ['_'.join(filename.split('_')[:2]) for filename in listdir(colour_equation_dir)]
    return correctable_labels


def apply_colour_equation(input_synthetic_photometry: 'pd.DataFrame',
                          photometric_system: Optional[Union[list, 'PhotometricSystem']] = None, output_path: str = '.',
                          output_file: str = 'corrected_photometry', output_format: Optional[str] = None,
                          save_file: bool = True, *, disable_info: bool = False, overwrite="yes") -> 'pd.DataFrame':
    """Apply the bundled DR3 colour equations to selected synthetic photometry.

    Args:
        input_synthetic_photometry (pandas.DataFrame): Photometry containing
            source_id and magnitude, flux and flux-error columns for each
            equation's target and colour passbands. File input is not accepted.
        photometric_system (PhotometricSystem or list): Current PhotometricSystem
            member or list of PhotometricSystem members to consider. Supply this
            explicitly; the None default does not infer systems from the input columns.
        output_path (str or pathlib.Path): Destination directory when saving;
            defaults to the current directory. Missing directories are created.
        output_file (str): Filename stem without an extension; defaults to
            'corrected_photometry'.
        output_format (str or None): 'csv', 'ecsv', 'fits' or 'xml'
            (VOTable), ignoring case and an initial dot. None selects CSV.
        overwrite (str): 'yes' or 'y' replaces existing files (default: 'yes').
            'no' or 'n' raises FileExistsError if any output exists. 'ask' prompts
            once before replacing existing files. Values are case-insensitive.
            Declining skips saving. With save_file=False, 'ask' emits a warning
            unless disable_info=True.
        save_file (bool): Save the result; defaults to True. False returns the
            corrected table without writing files.
        disable_info (bool): Suppress routine reader/writer messages, the correction
            progress bar and the ignored-overwrite notice; defaults to False.

    Returns:
        pandas.DataFrame: Prepared photometry with supported target magnitudes,
        fluxes and flux errors corrected. The supplied DataFrame is unchanged;
        the result has a fresh default integer index.

    Raises:
        ValueError: Input is not a DataFrame or save arguments are invalid.
        TypeError: photometric_system is None or cannot be treated as a selection.
        KeyError: A selected equation requires an absent photometry column or
            configuration field.

    Notes:
        The function 'generate' already applies these equations automatically.
        Calling this function on that result applies them again; it does not
        detect earlier correction. Use photometry that has not already received
        the equation.
    """
    overwrite = validate_overwrite(overwrite)
    return _apply_colour_equation(input_synthetic_photometry=input_synthetic_photometry,
                                  photometric_system=photometric_system, output_path=output_path,
                                  output_file=output_file, output_format=output_format, save_file=save_file,
                                  disable_info=disable_info, overwrite=overwrite)


def _apply_colour_equation(input_synthetic_photometry: 'pd.DataFrame',
                           photometric_system: Union[list, 'PhotometricSystem'] = None, output_path: str = '.',
                           output_file: str = 'corrected_photometry', output_format: Optional[str] = None,
                           save_file: bool = True, disable_info=False, metadata_records=None, *,
                           overwrite="yes") -> 'pd.DataFrame':
    """Apply colour equations with internal progress and provenance options.

    Input, system selection, output arguments and returned photometry follow
    apply_colour_equation. Prepare a DataFrame copy, load only matching DR3 equations,
    replace each target passband's photometry, and optionally save the result.

    Args:
        disable_info (bool): Suppress routine reader/writer messages and the
            correction progress bar; defaults to False.
        metadata_records (list[dict] or None): Append system, method='colour_equation'
            and equation-file records for the generation pipeline. None collects
            no records. This list is separate from the returned DataFrame's attrs.

    Returns:
        pandas.DataFrame: Photometry with the configured DR3 corrections applied.

    Notes:
        Providing an empty system list leaves the photometry values unchanged.
        A non-empty explicit system selection is needed to apply any equations.
        The method does not infer a selection when photometric_system is None.
    """
    overwrite = validate_overwrite(overwrite)
    function = apply_colour_equation
    validate_save_arguments(function.__defaults__[2], output_file, function.__defaults__[3], output_format, save_file)
    input_synthetic_photometry, extension = DataFrameReader(input_synthetic_photometry, function, False,
                                                            disable_info=disable_info).read()
    systems_to_correct = __get_systems_to_correct(photometric_system)
    systems_details = __fill_systems_details(systems_to_correct)
    output_df = __generate_output_df(input_synthetic_photometry, systems_details, disable_info=disable_info)
    if metadata_records is not None:
        metadata_records.extend({'system': label, 'method': 'colour_equation',
                                 'file': _get_colour_equation_file(label)} for label in systems_details)
    output_data = PhotometryData(output_df)
    output_data.data = cast_output(output_data)
    output_data.save(save_file, output_path, output_file, output_format, extension, disable_info=disable_info,
                     overwrite=overwrite)
    return output_data.data
