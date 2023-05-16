"""
config.py
====================================
Module to work with the converter configuration.
"""
from pathlib import Path
from typing import Union
from xml.etree import ElementTree

import numpy as np
import pandas as pd


def parse_configuration_file(xml_file: Union[Path, str], columns: list) -> pd.DataFrame:
    """
    Parse the input XML file and store the result in a pandas DataFrame with the given columns.

    Args:
        xml_file (Path/str): Path to the XML configuration file.
        columns (list): List of columns of the configuration file.

    Returns:
        DataFrame: A DataFrame with the given columns and their corresponding values.
    """
    xtree = ElementTree.parse(xml_file)
    root = xtree.getroot()
    rows = []

    for xp in root.iter():
        if xp.tag in ['bpConfig', 'rpConfig']:
            results = []
            for element in columns:
                lower_element = element.lower()
                if 'range' in lower_element:
                    result = extract_range(xp, element)
                elif 'matrix' in lower_element:
                    result = extract_matrix(xp, element)
                else:
                    result = extract_value(xp, element)
                results.append(result)
            rows.append({columns[i]: results[i] for i in range(len(columns))})
    return pd.DataFrame(rows, columns=columns)


def extract_range(xp: ElementTree.Element, element: str) -> np.ndarray:
    """
    Extract the range values for a given element.

    Args:
        xp (Element): Element from the XML tree.
        element (str): Column name to extract the range values for.

    Returns:
        ndarray: Range values, or None if the element or its attributes are not found.
    """
    if xp is not None and xp.find(element) is not None:
        from_value = float(xp.find(element).get('from'))
        to_value = float(xp.find(element).get('to'))
        return np.array((from_value, to_value))
    else:
        return None


def extract_matrix(xp: ElementTree.Element, column: str) -> np.ndarray:
    """
    Extract the matrix values for a given element.

    Args:
        xp (Element): Element from the XML tree.
        column (str): Column name to extract the matrix values for.

    Returns:
        ndarray: Matrix values, or None if the element or its values are not found.
    """
    if xp is not None and xp.find(column) is not None:
        values = [float(value.text) for value in xp.find(column).iter('value')]
        return np.array(values)
    else:
        return None


def extract_value(xp: ElementTree.Element, column: str) -> str:
    """
    Extract the value for a given element.

    Args:
        xp (Element): Element from the XML tree.
        column (str): Column name to extract the value for.

    Returns:
        str: Value of the element, or None if the element is not found.
    """
    if xp is not None and xp.find(column) is not None:
        return xp.find(column).text
    else:
        return None


def load_config(_path: str) -> pd.DataFrame:
    """
    Load the configuration for the converter functionality.

    Args:
        _path (str): Path to the configuration file.

    Returns:
        DataFrame: A DataFrame containing the columns and values of the configuration file.
    """
    return parse_configuration_file(_path, ['uniqueId', 'dimension', 'range', 'normalizedRange',
                                            'transformedSetDimension', 'transformationMatrix'])


def get_config(config: pd.DataFrame, _id: int) -> pd.DataFrame:
    """
    Access the group of rows in the configuration for the given ID.

    Args:
        config (DataFrame): A DataFrame containing the configuration columns and values.
        _id (int): An identifier of a set of configurations.

    Returns:
        DataFrame: A DataFrame containing the configuration values.
    """
    return config.loc[config['uniqueId'] == str(_id)]
