"""
config.py
====================================
Module to work with the converter configuration.
"""
import xml.etree.ElementTree as et
from collections import namedtuple
from pathlib import Path
from typing import Tuple, Optional, List, Union

import numpy as np
import pandas as pd


def __convert_to_dict(obj):
    if obj.__class__.__name__ == 'Tuple':
        return {key: __convert_to_dict(val) for key, val in obj._asdict().items()}
    elif hasattr(obj, '__dict__'):
        return {key: __convert_to_dict(val) for key, val in obj.__dict__.items()}
    else:
        return obj


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


def get_bands_config(bases_config):
    if hasattr(bases_config, 'hermiteFunction'):
        return bases_config.hermiteFunction
    elif hasattr(bases_config, 'basisDefinition'):
        return bases_config.basisDefinition.spline
    else:
        raise ValueError('Bases configuration type not implemented.')


def get_unique_id(config: pd.DataFrame, _id: int) -> pd.DataFrame:
    """
    Access the group of rows in the configuration for the given ID.

    Args:
        config (DataFrame): A DataFrame containing the configuration columns and values.
        _id (int): An identifier of a set of configurations.

    Returns:
        DataFrame: A DataFrame containing the configuration values.
    """
    return config.loc[config['uniqueId'] == _id]
