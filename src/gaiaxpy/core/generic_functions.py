"""
generic_functions.py
====================================
Module to hold some functions used by different subpackages.
"""

import sys
from ast import literal_eval
from collections import namedtuple
from os.path import join
from pathlib import Path
from string import capwords
from typing import Optional, Union, Tuple, List
from xml.etree import ElementTree as et

import numpy as np
import pandas as pd
from numpy import ndarray

from gaiaxpy.config.paths import filters_path, config_path
from gaiaxpy.core.custom_errors import InvalidBandError
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.generator.config import get_additional_filters_path
from gaiaxpy.spectrum.utils import _correlation_to_covariance_dr3int5

# Verifying the function is valid first, will help when adding new functions
PHOTOMETRY_FUNCTIONS = ['generate', '_generate']
CHOLESKY_FUNCTIONS = ['get_inverse_covariance_matrix', 'get_inverse_square_root_covariance_matrix']
OTHER_FUNCTIONS = ['calibrate', 'convert']  # The ones that accept truncation and with_correlation arguments
ALL_ADD_COLS_FUNCTIONS = PHOTOMETRY_FUNCTIONS + CHOLESKY_FUNCTIONS + OTHER_FUNCTIONS


def _get_built_in_systems() -> list:
    av_sys = open(join(config_path, 'available_systems.txt'), 'r')
    return av_sys.read().splitlines()


def _is_built_in_system(system):
    return system in _get_built_in_systems()


def cast_output(output):
    cast_dict = {'source_id': 'int64', 'solution_id': 'int64'}
    cast_dict_keys = cast_dict.keys()
    df = output if isinstance(output, pd.DataFrame) else output.data
    for column in df.columns:
        if column in cast_dict_keys:
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
    if isinstance(str_array, str) and len(str_array) >= 2 and str_array[0] == '(' and str_array[1] == '(':
        return str_to_matrix(str_array)
    elif isinstance(str_array, str):
        try:
            return np.fromstring(str_array[1:-1], sep=',')
        except Exception:  # np.fromstring may not raise an error but only show a warning depending on the version
            raise ValueError('Input cannot be converted to array.')
    elif isinstance(str_array, float):
        return float('NaN')
    else:
        raise ValueError('Unhandled type.')


def validate_pwl_sampling(sampling):
    # Receives a NumPy array. Validates sampling in pwl.
    min_sampling_value = -10
    max_sampling_value = 70
    if sampling is None:
        raise ValueError("Sampling can't be None.")
    if len(sampling) == 0:
        raise ValueError('Sampling must contain at least one point.')
    # Must be a numpy array
    if not isinstance(sampling, ndarray):
        raise TypeError('Sampling must be a NumPy array.')
    # Array must be sorted in ascending order
    if not np.array_equal(sampling, np.sort(sampling)):
        raise ValueError('Sampling must be in ascending order.')
    min_value = sampling[0]
    max_value = sampling[-1]
    if min_value < min_sampling_value or max_value > max_sampling_value:
        raise ValueError(f'Wrong value for sampling. Sampling accepts an array of values where the minimum value is '
                         f'{min_sampling_value} and the maximum is {max_sampling_value}.')


def validate_wl_sampling(sampling):
    min_value = 330
    max_value = 1050
    # Check sampling
    if sampling is not None:
        if sampling[0] >= sampling[-1]:
            raise ValueError('Sampling should be a non-decreasing array.')
        elif sampling[0] < min_value or sampling[-1] > max_value:
            raise ValueError(f'Wrong value for sampling. Sampling accepts an array of values where the minimum value '
                             f'is {min_value} and the maximum is {max_value}.')


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


def _get_system_label(name):
    """
    Get the label of the photometric system.

    Returns:
        str: A short description of the photometric system.
    """

    def snake_to_pascal(word):
        return capwords(word.replace("_", " ")).replace(" ", "")

    return snake_to_pascal(name) if _is_built_in_system(name) else name


def _get_system_path(is_built_in):
    return filters_path if is_built_in else get_additional_filters_path()


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
            raise ValueError("Input must have a decimal part of exactly .0")
    if isinstance(array, np.ndarray):
        n_dim = array.ndim
        if array.size == 0 or n_dim == 2:  # Either empty or already a matrix
            return array
        elif n_dim == 1:
            array_size = int(array_size)
            matrix = np.zeros((array_size, array_size))
            np.fill_diagonal(matrix, 1.0)  # Add values in diagonal
            k = 0 if contains_diagonal(array_size, array) else -1  # Diagonal offset (from Numpy documentation)
            matrix[np.tril_indices(array_size, k=k)] = array
            transpose = matrix.transpose()
            transpose[np.tril_indices(array_size, -1)] = matrix[np.tril_indices(array_size, -1)]
            return transpose
    raise TypeError('Wrong argument types. Must be np.ndarray and integer or float.')


def _extract_systems_from_data(data_columns, photometric_system=None):
    if isinstance(photometric_system, list):
        return [system.get_system_label() for system in photometric_system]
    src = 'source_id'
    columns = list(data_columns.copy())
    if src in columns:
        columns.remove(src)
    if photometric_system:
        photometric_system = photometric_system if isinstance(photometric_system, list) else [photometric_system]
        systems = [system.get_system_label() for system in photometric_system]
    else:
        # Infer photometric_system from the data
        column_list = [column.split('_')[0] for column in columns]
        systems = list(dict.fromkeys(column_list))
    return systems


def correlation_from_covariance(covariance):
    if covariance is None:
        return None
    v = np.sqrt(np.diag(covariance))
    outer_v = np.outer(v, v)
    correlation = covariance / outer_v
    correlation[covariance == 0] = 0
    return correlation


def correlation_to_covariance(correlation: np.ndarray, error: np.ndarray, stdev: float) -> np.ndarray:
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
    if correlation is None or (isinstance(correlation, float) and pd.isna(correlation)):
        return None
    if correlation.ndim == 1:
        size = get_matrix_size_from_lower_triangle(correlation)
        new_matrix = np.zeros((size, size))
        new_matrix[np.tril_indices(size, k=-1)] = correlation
        new_matrix += new_matrix.T
        new_matrix += np.diag(np.ones(size), k=0)
        correlation = new_matrix
    if correlation.ndim == 2:
        return _correlation_to_covariance_dr3int5(correlation, error, stdev)
    else:
        raise ValueError('Dimensions of input correlation must be either 1 or 2.')


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


def validate_additional_columns(additional_columns, function, **kwargs):
    systems = None
    additional_columns = format_additional_columns(additional_columns)
    function_name = function.__name__
    if function_name not in ALL_ADD_COLS_FUNCTIONS:
        raise ValueError(f'Function {function_name} does not accept additional columns.')
    if function_name in PHOTOMETRY_FUNCTIONS:
        systems = kwargs['photometric_system']
    if systems and function.__name__ not in ['_generate', 'generate']:
        raise ValueError('Systems will only work with photometry-related functions.')


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


def validate_photometric_system(photometric_system):
    """
    Ensure photometric system input isn't empty.
    """
    if photometric_system in (None, [], ''):
        raise ValueError('At least one photometric system is required as input.')


def rename_with_required(data, additional_columns):
    return data.rename(columns=reverse_simple_add_col_dict(additional_columns))


def is_array_empty(array):
    return array is None or (not isinstance(array, np.ndarray) and pd.isna(array)) or (isinstance(array, np.ndarray)
                                                                                       and len(array) == 0)


def is_variable_empty(var):
    return var is None or pd.isna(var)


def get_bands_config(bases_config):
    if hasattr(bases_config, 'hermiteFunction'):
        return bases_config.hermiteFunction
    elif hasattr(bases_config, 'basisDefinition'):
        return bases_config.basisDefinition.spline
    else:
        raise ValueError('Bases configuration type not implemented.')


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


def __create_namedtuple(label: str, data: dict) -> namedtuple:
    """
    Create a named tuple with the given label and data.

    :param label: A string representing the label to use for the named tuple.
    :type label: str
    :param data: A dictionary representing the data to be stored in the named tuple.
    :type data: dict
    :return: A named tuple with the given label and data.
    :rtype: namedtuple
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
                   return_dict=False) -> namedtuple:
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


def parse_config(xml_file: Union[Path, str]) -> namedtuple:
    """
    Parses a configuration file in XML format and returns a named tuple with the settings. It returns the values for
    all the tags present in the file.

    :param xml_file: The path to the XML file to parse.
    :type xml_file: Union[Path, str]
    :return: A named tuple containing the configuration settings.
    :rtype: namedtuple
    """
    x_root = __get_file_root(xml_file)
    outer_title = x_root.tag.split('}')[1]
    return __parse_config(x_root, outer_title=outer_title)


def format_sampled_output(spectra_series, with_correlation):
    positions = spectra_series.iloc[0].get_positions()
    spectra_type = get_spectra_type(spectra_series.iloc[0])
    spectra_series = spectra_series.map(lambda x: x.spectrum_to_dict(with_correlation))
    spectra_df = pd.DataFrame(spectra_series.tolist())
    spectra_df.attrs['data_type'] = spectra_type
    return spectra_df, positions
