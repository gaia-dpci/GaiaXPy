"""
config.py
====================================
Module to work with the converter's configuration.
"""

import numpy as np
import pandas as pd
import xml.etree.ElementTree as et


def parse_configuration_file(xml_file, columns):
    """
    Parse the input XML file and store the result in a pandas DataFrame with the given columns.

    Args:
        xml_file (str): Path to the XML configuration file.
        columns (list): List of columns of the configuration file.

    Returns:
        DataFrame: A DataFrame with the given columns and their corresponding values.
    """
    xtree = et.parse(xml_file)
    xroot = xtree.getroot()
    rows = []

    for xp in xroot.iter():
        if xp.tag == 'bpConfig' or xp.tag == 'rpConfig':
            results = []
            for element in columns[:]:
                if 'range' in element.lower():
                    if xp is not None and xp.find(element) is not None:
                        result = (
                            float(
                                xp.find(element).get('from')), float(
                                xp.find(element).get('to')))
                        results.append(np.array(result))
                    else:
                        results.append(None)
                elif 'matrix' in element.lower():
                    if xp is not None and xp.find(element) is not None:
                        values = []
                        for value in xp.find(element).iter('value'):
                            values.append(float(value.text))
                        results.append(np.array(values))
                    else:
                        results.append(None)
                else:
                    if xp is not None and xp.find(element) is not None:
                        results.append(xp.find(element).text)
                    else:
                        results.append(None)
            rows.append({columns[i]: results[i]
                         for i, _ in enumerate(columns)})
    return pd.DataFrame(rows, columns=columns)


def load_config(path):
    """
    Load the configuration for the converter functionality.

    Args:
        path (str): Path to the configuration file.

    Returns:
        DataFrame: A DataFrame containing the columns and values of the configuration file.
    """
    return parse_configuration_file(path,
                                    ['uniqueId',
                                     'dimension',
                                     'range',
                                     'normalizedRange',
                                     'transformedSetDimension',
                                     'transformationMatrix'])


def get_config(config, id):
    """
    Access the group of rows in the configuration for the given ID.

    Args:
        config (str): A DataFrame containing the configuration columns and values.
        id (int): An identifier of a set of configurations.

    Returns:
        DataFrame: A DataFrame containing the configuration values.
    """
    return config.loc[config['uniqueId'] == str(id)]
