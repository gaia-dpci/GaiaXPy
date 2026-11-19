"""
generic_functions.py
====================================
Module to hold some functions used by different subpackages.
"""

import re
import sys
import types
from ast import literal_eval
from collections import namedtuple
from itertools import chain
from pathlib import Path
from typing import Optional, Union, Tuple, List
from xml.etree import ElementTree as et

import numpy as np
import pandas as pd

from gaiaxpy.core.custom_errors import InvalidBandError
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.utils import correlation_to_covariance_dr3int5


def cast_output(output):
    cast_dict = {'source_id': 'int64', 'solution_id': 'int64'}
    df = output if isinstance(output, pd.DataFrame) else output.data
    for column in cast_dict.keys():
        if column in df.columns:
            df[column] = df[column].astype(cast_dict[column])
    return df


def parse_band(band):
    if isinstance(band, str):
        band = band.lower()
    elif isinstance(band, list) and len(band) == 1:
        band = band[0].lower()
    if band in BANDS:
        return band
    else:
        raise InvalidBandError(band)


def str_to_matrix(str_matrix):
    """
    Convert a string of the form ((1,2,3),(4,5,6),(7,8,9)) to a NumPy matrix.
    """
    # Replace nan to None so the string can be evaluated
    str_matrix = str_matrix.replace('nan', 'None')
    evaluated = literal_eval(str_matrix)
    evaluated = np.array(evaluated)
    evaluated = np.where(evaluated is None, np.nan, evaluated)
    return np.array(evaluated)


def str_to_array(str_array):
    if isinstance(str_array, np.ndarray):
        return str_array
    if isinstance(str_array, list):
        return np.asarray(str_array)
    if str_array is None:
        return float('NaN')
    if pd.isna(str_array):
        return float('NaN')
    if isinstance(str_array, float):
        return float('NaN')
    if isinstance(str_array, str) and len(str_array) >= 2 and str_array[0:2] == '((':
        return str_to_matrix(str_array)
    elif isinstance(str_array, str):
        try:
            return np.fromstring(str_array[1:-1], sep=',')
        except Exception:  # np.fromstring may not raise an error but only show a warning depending on the version
            raise ValueError('Input cannot be converted to array.')
    else:
        raise ValueError(f'Unhandled type: {type(str_array).__name__}.')


def _validate_sampling_grid(sampling, minimum, maximum):
    """Validate a one-dimensional, finite, non-decreasing sampling grid."""
    if sampling is None:
        raise ValueError('Sampling cannot be None.')
    if not isinstance(sampling, np.ndarray):
        raise TypeError('Sampling must be a NumPy array.')
    if sampling.ndim != 1 or sampling.size == 0:
        raise ValueError('Sampling must be a non-empty one-dimensional array.')
    if sampling.dtype.kind not in 'iuf' or not np.isfinite(sampling).all():
        raise ValueError('Sampling must contain finite real numbers.')
    if np.any(sampling[1:] < sampling[:-1]):
        raise ValueError('Sampling must be in ascending order.')
    if sampling[0] < minimum or sampling[-1] > maximum:
        raise ValueError(f'Sampling values must be between {minimum} and {maximum}.')


def validate_pwl_sampling(sampling):
    _validate_sampling_grid(sampling, -10, 70)


def validate_wl_sampling(sampling):
    if sampling is None:
        return
    grid = np.asarray(sampling)
    _validate_sampling_grid(grid, 330, 1050)
    if grid[0] == grid[-1]:
        raise ValueError('Wavelength sampling must contain at least two distinct positions.')


def _warning(message):
    print(f'UserWarning: {message}', file=sys.stderr)


def get_spectra_type(spectra):
    """
    Get the spectra type.

    Args:
        spectra (object): A spectrum or a spectra list.

    Returns:
        str: Spectrum type (e.g. AbsoluteSampledSpectrum).
    """
    if isinstance(spectra, list):
        spectrum = spectra[0]
    elif isinstance(spectra, dict):
        spectrum = spectra[list(spectra.keys())[0]]
    else:
        spectrum = spectra
    return spectrum.__class__


# AVRO files include the values in the diagonal, whereas others don't
def array_to_symmetric_matrix(array, array_size):
    """
    Convert the input 1D array into a 2D matrix. The array is assumed to store only the unique elements of a symmetric
        matrix (i.e. all elements above the diagonal plus the diagonal) in column major order. A full 2D matrix is
        returned symmetric with respect to the diagonal.

    Args:
        array (ndarray): 1D array.
        array_size (int): number of rows/columns in the output matrix.

    Returns:
        array of arrays: a full 2D matrix.

    Raises:
        TypeError: If array is not of type np.ndarray.
    """

    def contains_diagonal(_array_size, _array):
        return not len(_array) == len(np.tril_indices(_array_size - 1)[0])

    # Is NaN size or NaN array
    if pd.isna(array_size) or (isinstance(array, float) and pd.isna(array)):
        return array
    if isinstance(array_size, float):  # If the missing band source is present, floats may be returned when parsing
        float_size = float(array_size)
        array_size = int(array_size)
        if float_size != array_size:
            raise ValueError('Input must have a decimal part of exactly .0')
    if isinstance(array, np.ndarray):
        n_dim = array.ndim
        if array.size == 0 or n_dim == 2:  # Either empty or already a matrix
            return array
        elif n_dim == 1:
            n = int(array_size)
            matrix = np.eye(n)
            has_diag = contains_diagonal(n, array)
            k = 0 if has_diag else -1
            i, j = np.tril_indices(n, k=k)
            # Avoid transpose
            matrix[i, j] = array
            matrix[j, i] = array

        return matrix
    raise TypeError(f'Wrong argument types. Must be np.ndarray and integer or float, '
                    f'but types are {type(array).__name__} and {type(array_size).__name__}.')


def lower_correlation_from_covariance(covariance: np.ndarray) -> np.ndarray | None:
    if covariance is None:
        return None

    i, j = np.tril_indices(covariance.shape[0], k=-1)
    stdev = np.sqrt(np.diag(covariance))
    denominator = stdev[i] * stdev[j]

    correlation = np.zeros_like(denominator, dtype=np.result_type(covariance, float))
    np.divide(covariance[i, j], denominator, out=correlation, where=denominator != 0)

    return correlation


def correlation_to_covariance(correlation: np.ndarray, error: np.ndarray, stdev: float) -> Optional[np.ndarray]:
    """
    Compute the covariance matrix from the correlation values.

    If the input correlation values are a 1D array, the values are assumed to be the lower triangle of a
    symmetric matrix (excluding the diagonal). The array will be internally converted to a full correlation matrix.

    Args:
        correlation (ndarray): A 2D numpy array of shape (n, n) representing the correlation matrix.
            Alternatively, a 1D numpy array of length n*(n-1)/2 representing the lower triangle of a
            symmetric correlation matrix (excluding the diagonal).
        error (ndarray): A 1D numpy array of length n containing the flux errors.
        stdev (float): The scaling factor for the errors.

    Returns:
        ndarray: A 2D numpy array of shape (n, n) representing the covariance matrix.

    Raises:
        ValueError: If the dimensions of input correlation are not either 1 or 2.
    """
    if correlation is None:
        return None

    # Handles a scalar NaN sometimes produced by pandas
    if np.isscalar(correlation):
        if np.isnan(correlation):
            return None
        raise ValueError("Correlation must be a 1D or 2D array.")

    if correlation.ndim == 2:
        return correlation_to_covariance_dr3int5(correlation, error, stdev)

    if correlation.ndim != 1:
        raise ValueError("Correlation must be a 1D or 2D array.")

    size = get_matrix_size_from_lower_triangle(correlation)
    rows, cols = np.tril_indices(size, k=-1)

    correlation_matrix = np.eye(size, dtype=correlation.dtype)
    correlation_matrix[rows, cols] = correlation
    correlation_matrix[cols, rows] = correlation

    return correlation_to_covariance_dr3int5(correlation_matrix, error, stdev)


def get_matrix_size_from_lower_triangle(array):
    """
    Compute the size of a symmetric matrix from an array containing the values of its lower triangle, excluding the
    diagonal.

    Args:
        array (ndarray): An array of length n*(n-1)/2 representing the lower triangle of an n x n symmetric matrix,
            excluding the diagonal.

    Returns:
        int: The size n of the symmetric matrix.

    Raises:
        ValueError: If the length of array is not a valid input for a symmetric matrix lower triangle.
    """
    return int((np.sqrt(1 + 8 * len(array)) + 1) / 2)


def get_file_extension(file_path):
    """
    Return the underlying format, ignoring one gzip suffix for supported inputs.
    """
    path = Path(file_path)
    extension = path.suffix.lower().lstrip('.')
    if extension == 'gz':
        underlying = Path(path.stem).suffix.lower().lstrip('.')
        if underlying in ('csv', 'ecsv', 'fits', 'xml'):
            return underlying
    return standardise_extension(extension) if extension else ''


def standardise_extension(_extension):
    """
    Standardise the provided extension which can contain or not an initial dot, and can contain a mix of uppercase and
    lowercase letters.

    Args:
        _extension (str): File extension which may or may not contain an initial dot.

    Returns:
        str: The extension in lowercase letters and with no initial dot (e.g.: 'csv').
    """
    try:
        _extension = _extension[1:] if _extension[0] == '.' else _extension  # Remove initial dot if present
        return _extension.lower()
    except IndexError:
        raise ValueError(f"Extension '{_extension}' could not be parsed appropriately.")


def reverse_simple_add_col_dict(d):
    def __reverse_error(v):
        raise ValueError(f'List length should be one, but is {len(v)}.')

    return {value[0]: key if len(value) == 1 else __reverse_error(value) for key, value in d.items()}


def convert_values_to_lists(d):
    for key, value in d.items():
        if not isinstance(value, list):
            d[key] = [value]
    return d


def format_additional_columns(additional_columns: Optional[Union[str, list, dict]]):
    """
    Ensure additional columns are in the expected format. Output should be a dictionary, values in the dictionary
    should become lists to work with nested AVRO keys.
    """
    if additional_columns is None:
        return dict()
    if isinstance(additional_columns, str):
        return {additional_columns: [additional_columns]}
    if isinstance(additional_columns, list):
        return {v: [v] for v in additional_columns}
    if isinstance(additional_columns, dict):
        return convert_values_to_lists(additional_columns)
    else:
        raise ValueError(f'Additional columns type is {type(additional_columns).__name__}. This is not allowed.')


def validate_photometric_system(photometric_system) -> list:
    """
    Return a list of current registry members belonging to the same Gaia release.

    Removed or replaced additional-system objects raise ValueError, even if
    caller code still holds a reference to them.
    """
    systems = photometric_system.copy() if isinstance(photometric_system, list) else [photometric_system]
    if photometric_system is None or not systems:
        raise ValueError('At least one photometric system is required as input.')
    from gaiaxpy.photometric_system.photometric_system import AutoName, PhotometricSystem

    invalid = [repr(system) if isinstance(system, str) else type(system).__name__
               for system in systems if not isinstance(system, AutoName)]
    if invalid:
        raise TypeError('photometric_system must be a PhotometricSystem member or a list of members. '
                        f"Invalid entries: {', '.join(invalid)}.")

    for system in systems:
        if system not in PhotometricSystem:
            raise ValueError(f'Photometric system {system.name!r} is not currently loaded. '
                             'Select a current member from PhotometricSystem.')
    return systems


def rename_with_required(data, additional_columns):
    return data.rename(columns=reverse_simple_add_col_dict(additional_columns))


def is_array_empty(array):
    return array is None or (not isinstance(array, np.ndarray) and pd.isna(array)) or (isinstance(array, np.ndarray)
                                                                                       and len(array) == 0)


def is_variable_empty(var):
    return var is None or pd.isna(var)


def __range_to_output(d: dict) -> Tuple[float, float]:
    """
    Extract the 'from' and 'to' values from a dictionary `d` and return them as a tuple of two floats.

    :param d: A dictionary containing the keys 'from' and 'to', whose values are assumed to be convertible to floats.

    :return: A tuple of two floats representing the 'from' and 'to' values from the dictionary.

    :raises KeyError: If the 'from' or 'to' key is not present in the input dictionary.
    :raises ValueError: If the 'from' or 'to' value is not a valid float.
    """
    return float(d['from']), float(d['to'])


def __is_empty_string(string: str):
    def replace_empty_characters(s):
        separator_chars = ['\n', '\t']
        for ec in separator_chars:
            s = s.replace(ec, '')
        return s

    string = replace_empty_characters(string)
    for char in string:
        if not char.isspace():
            return False
    return True


def __parse_text_number(text):
    try:
        integer_value = int(text)
        return integer_value
    except ValueError:
        try:
            float_value = float(text)
            return float_value
        except ValueError:
            return text


def __add_element_to_dict(element: et.Element, output_dict: dict):
    """
    Add an element to a dictionary based on its tag and attributes.

    :param element: The element to add to the dictionary.
    :param output_dict: The dictionary to add the element to.

    :return: None

    :raises ValueError: If the element tag is not recognised.
    """
    if element.attrib:
        output_dict[element.tag] = __range_to_output(element.attrib)
    elif 'knots' in element.tag.lower():
        values = [float(value.text) for value in element.iter('value')]
        output_dict[element.tag] = tuple(values)
    # In some cases text is a string containing only a linebreak followed by blank spaces. In other cases, it can be
    # an integer or float as string, or plain text
    elif element.text:
        try:
            output_dict[element.tag] = float(element.text) if '.' in element.text else int(element.text)
        except (ValueError, TypeError):
            if __is_empty_string(element.text):
                output_dict[element.tag] = __parse_config(element, return_dict=True)
            else:
                output_dict[element.tag] = element.text
    else:
        raise ValueError(f'Unrecognized tag: {element.tag}')


def __iterative_find(x_root: et.Element, tag_list: List[str]) -> Optional[et.Element]:
    """
    Iteratively search for nested elements in an XML tree.
    :param x_root: The root element of the XML tree to search in.
    :type x_root: Element
    :param tag_list: A list of tag names to search for, in order.
    :type tag_list: List[str]
    :return: The first nested element that matches all tags in the `tag_list`, or `None` if no such element is found.
    :rtype: Element or None
    :raises: No exceptions are raised by this function.
    """

    def find_in_root(_x_root: et.Element, _tag: str) -> Optional[et.Element]:
        """
        Find the first child element of `_x_root` with the given `tag` name.
        :param _x_root: The root element to search in.
        :type _x_root: Element
        :param _tag: The tag name to search for.
        :type _tag: str
        :return: The first child element of `x_root` with the given `tag` name, or `None` if not found.
        :rtype: Element or None
        :raises: No exceptions are raised by this function.
        """
        return _x_root.find(_tag)

    result = x_root
    for tag in tag_list:
        result = find_in_root(result, tag)
        if result is None:
            break
    return result


def __generate_iterative_output(x_root, outer_tags):
    def is_matrix_or_knots(_tag):
        return 'matrix' in _tag.lower() or 'knots' == _tag.lower()

    _output = {}
    for tag in outer_tags:
        found_elements = __iterative_find(x_root, [tag])
        _output[tag] = dict()
        if len(found_elements) == 0 and not found_elements.attrib:
            _output[tag] = __parse_text_number(found_elements.text)
        elif len(found_elements) == 0 and found_elements.attrib:
            _output[tag] = __range_to_output(found_elements.attrib)
        elif is_matrix_or_knots(found_elements.tag):
            values = [float(value.text) for value in found_elements.iter('value')]
            _output[found_elements.tag] = np.array(values)
        else:
            for element in found_elements:
                __add_element_to_dict(element, _output[tag])
    return _output


def __generate_array_output(x_root, outer_tags):
    output_array = [el.text for el in x_root.findall(outer_tags[0])]
    try:
        output_array = tuple([float(el) for el in output_array])
    except ValueError:
        output_array = tuple(output_array)  # Elements can't be parsed to floats, may be actual strings
    return output_array


def __create_namedtuple(label: str, data: dict) -> Tuple:
    """
    Create a named tuple with the given label and data.

    :param label: A string representing the label to use for the named tuple.
    :type label: str
    :param data: A dictionary representing the data to be stored in the named tuple.
    :type data: dict
    :return: A named tuple with the given label and data.
    :rtype: tuple
    """

    def __add_matrix_to_config(_data, _xp):
        config_str = f'{_xp}Config'
        hermite_function = _data.get('basisDefinition', {}).get('hermiteFunction', {})
        _config = hermite_function.get(config_str, {})
        if _config and 'transformationMatrix' not in _config:
            dimension = _config.get('dimension', None)
            if dimension:
                _config['transformationMatrix'] = np.identity(dimension)
                _config['transformedSetDimension'] = dimension

    for xp in ['bp', 'rp']:
        __add_matrix_to_config(data, xp)
    for key, value in data.items():
        if isinstance(value, dict):
            data[key] = __create_namedtuple('Tuple', value)
    CalTuple = namedtuple(label, data)
    cal_tuple = CalTuple(**data)
    return cal_tuple


def __parse_config(x_root: et.Element, outer_tags: Optional[List[str]] = None, outer_title: Optional[str] = None,
                   return_dict=False) -> Tuple:
    """
    Parse the configuration in x_root. If no outer_tags list is given, the function will parse every tag in the input
    x_root.
    """
    outer_tags = list(child.tag for child in x_root) if not outer_tags else outer_tags
    is_array = len(outer_tags) > 1 and len(set(outer_tags)) == 1
    _output = __generate_array_output(x_root, outer_tags) if is_array else __generate_iterative_output(x_root,
                                                                                                       outer_tags)
    outer_title = outer_title if outer_title else 'Internal'
    return _output if return_dict else __create_namedtuple(outer_title, _output)


def __get_file_root(xml_file: Union[Path, str]):
    """
    Parse an XML file and return its root element.

    :param xml_file: Path to the XML file to parse.
    :type xml_file: str

    :return: The root element of the parsed XML file.
    :rtype: Element

    :raises FileNotFoundError: If the specified XML file does not exist.
    :raises ElementTree.ParseError: If the specified XML file is not well-formed.
    """
    xtree = et.parse(xml_file)
    return xtree.getroot()


def parse_config(xml_file: Union[Path, str]) -> Tuple:
    """
    Parses a configuration file in XML format and returns a named tuple with the settings. It returns the values for
    all the tags present in the file.

    :param xml_file: The path to the XML file to parse.
    :type xml_file: Union[Path, str]
    :return: A named tuple containing the configuration settings.
    :rtype: tuple
    """
    if str(xml_file).lower().endswith('.npz'):
        with np.load(xml_file, allow_pickle=False) as archive:
            outer_title = archive['__root_name__'].item()
            tuple_paths = (
                set(archive['__tuple_paths__'].tolist())
                if '__tuple_paths__' in archive.files
                else set()
            )
            output = {}

            for key in archive.files:
                if key in {'__root_name__', '__tuple_paths__', '__gaiaxpy_metadata__'}:
                    continue

                value = archive[key]
                value = value.item() if value.ndim == 0 else value.copy()

                if key in tuple_paths:
                    value = tuple(value.tolist())

                parts = key.split('/')
                target = output

                for part in parts[:-1]:
                    target = target.setdefault(part, {})

                leaf = parts[-1]
                target[leaf[1:] if leaf.startswith('@') else leaf] = value

        def restore_attribute_ranges(value):
            if not isinstance(value, dict):
                return value

            if set(value) == {'from', 'to'}:
                return float(value['from']), float(value['to'])

            return {
                key: restore_attribute_ranges(child)
                for key, child in value.items()
            }

        return __create_namedtuple(
            outer_title,
            restore_attribute_ranges(output),
        )

    x_root = __get_file_root(xml_file)
    outer_title = x_root.tag.split('}')[1]
    return __parse_config(x_root, outer_title=outer_title)


def format_sampled_output(spectra, *, include_xp, with_correlation, with_stdev):
    # Get first spectrum to obtain the type and then put it back
    first_spectrum = next(spectra)
    spectra_type = get_spectra_type(first_spectrum)
    spectra = chain([first_spectrum], spectra)

    for name, value in (("include_xp", include_xp),
                        ("with_correlation", with_correlation),
                        ("with_stdev", with_stdev),):
        if not isinstance(value, bool):
            raise TypeError(f"The variable '{name}' must be a bool.")
    if include_xp:
        columns = ["source_id", "xp", "flux", "flux_error"]
    else:
        columns = ["source_id", "flux", "flux_error"]
    if with_correlation:
        columns.append("correlation")
    if with_stdev:
        columns.append("standard_deviation")

    records = (spectrum.spectrum_to_tuple(with_correlation) for spectrum in spectra)
    spectra_df = pd.DataFrame.from_records(records, columns=columns)
    spectra_df.attrs['data_type'] = spectra_type

    return spectra_df


def get_function_name(function):
    if isinstance(function, types.FunctionType):
        name = function.__name__
    elif isinstance(function, str):
        name = function
    else:
        raise TypeError('Function name must be a string or of function type')
    return name


def extract_system_identifier(column_names):
    """
    Extracts the system name (substring before '_mag_', '_flux_', or '_flux_error_' from a list of strings).

    :param column_names: The list of column names to process.
    :return: The system identifiers.
    :raises ValueError: If any column name doesn't match the expected pattern.
    """
    pattern = re.compile(r'^((?:USER_)?DR[34]_.+)_(?:flux_error|flux|mag|within_range)_.+$')
    extracted = []
    for name in column_names:
        match = pattern.search(name)
        if not match:
            raise ValueError(f'Column name does not match expected pattern: {name}')
        extracted.append(match.group(1))
    return extracted


def extract_systems_from_data(input_multi_photometry, release, photometric_system=None, return_label=True):
    """
    Return either a list of PhotometricSystem full labels (if return_label=True)
    or a list of PhotometricSystem objects (if return_label=False).
    """
    # Normalise release
    _release = release.upper()

    if return_label:
        # If explicit systems given
        if photometric_system:
            if isinstance(photometric_system, list):
                systems = [ps.get_system_full_label() for ps in photometric_system]
            else:
                systems = [photometric_system.get_system_full_label()]
        else:
            # Infer from column names
            data_columns = list(input_multi_photometry.columns)
            columns = [c for c in data_columns if c != 'source_id']
            systems_with_dups = extract_system_identifier(columns)
            # Use dict.fromkeys to preserve order and remove duplicates
            systems = list(dict.fromkeys(systems_with_dups))
        # Release consistency check
        mismatches = [s for s in systems if _release not in s.split('_')]
        if mismatches:
            raise ValueError(f"Mismatch between release and systems. Release is {_release}, but conflicting systems "
                             f"are: {', '.join(mismatches)}.")
        return systems

    if not photometric_system:
        raise ValueError(
            'No photometric systems provided. Cannot return enum objects without explicit PhotometricSystem'
            ' instances.')
    # Always return a list for consistency
    return photometric_system if isinstance(photometric_system, list) else [photometric_system]


def mag_to_flux(mag, zp):
    """
    Convert magnitude to flux.
    """
    return np.power(10, (-0.4 * (mag - zp)))


def format_list_to_str_msg(values):
    quoted = [f"'{x}'" for x in values]

    if len(quoted) == 0:
        return ""
    if len(quoted) == 1:
        return quoted[0]
    if len(quoted) == 2:
        return f"{quoted[0]} and {quoted[1]}"

    return f"{', '.join(quoted[:-1])}, and {quoted[-1]}"
