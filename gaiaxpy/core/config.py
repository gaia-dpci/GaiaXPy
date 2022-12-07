"""
config.py
====================================
Module to handle the calibrator and generator configuration files.
"""

from configparser import ConfigParser
from numbers import Number
from os import path

import numpy as np

from gaiaxpy.config.paths import config_path, filters_path
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.core.xml_utils import get_file_root, parse_array, get_array_text, get_xp_merge

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))


def get_file(label, key, system, bp_model, rp_model):
    """
    Get the file path corresponding to the given label and key.

    Args:
        label (str): Label of the photometric system or functionality (e.g.: 'Johnson' or 'calibrator').
        key (str): Type of file to load ('zeropoint', 'merge', 'sampling').
        system (str): Photometric system name, can be None in which case the generic configuration is loaded.
        bp_model (str): BP model.
        rp_model (str): RP model.

    Returns:
        str: Path of a file.
    """
    _config_parser = ConfigParser()
    _config_parser.read(path.join(config_path, 'config.ini'))
    file_name = _config_parser.get(label, key).format(label, key).replace('model', f'{bp_model}{rp_model}')
    if system:
        file_name = file_name.replace('system', system)
    else:
        file_name = file_name.replace('system_', '')
    return path.join(filters_path, file_name)


def _load_offset_from_xml(system, bp_model='v375wi', rp_model='v142r'):
    """
    Load the offset of a standard photometric system.
    """
    label = key = 'filter'
    file_path = get_file(label, key, system, bp_model, rp_model)
    x_root = get_file_root(file_path)
    return parse_array(x_root, 'fluxBias')


def _load_xpzeropoint_from_xml(system, bp_model='v375wi', rp_model='v142r'):
    """
    Load the zero-points for each band.

    Args:
        system (str): Name of the photometric system.

    Returns:
        ndarray: Zero-points in the XML file.
    """
    label = key = 'filter'
    file_path = get_file(label, key, system, bp_model, rp_model)
    x_root = get_file_root(file_path)
    zeropoints = parse_array(x_root, 'zeropoints')
    bands = get_array_text(x_root, 'bands')
    return bands, zeropoints


def _load_xpmerge_from_xml(system=None, bp_model=None, rp_model='v142r'):
    """
    Load the XpMerge table.

    Args:
        system (str): Name of the photometric system if it corresponds.

    Returns:
        ndarray: Array containing the sampling grid values.
        dict: A dictionary containing the XpMerge table with one entry for BP and one for RP.
    """
    if not bp_model:
        bp_model = 'v375wi'
    label = key = 'filter'
    file_path = get_file(label, key, system, bp_model, rp_model)
    x_root = get_file_root(file_path)
    sampling_grid, bp_merge, rp_merge = get_xp_merge(x_root)
    return sampling_grid, dict(zip(BANDS, [bp_merge, rp_merge]))


def _load_xpsampling_from_csv(
        label,
        system=None,
        bp_model=None,
        rp_model='v142r'):
    """
    Load the XpSampling table as provided by PMN in CSV.

    Args:
        label (str): Label of the photometric system or functionality.

    Returns:
        dict: A dictionary containing the XpSampling table with one entry for BP and one for RP.
    """
    if not bp_model:
        bp_model = 'v375wi'
    file_name = get_file(label, 'sampling', system, bp_model, rp_model)
    _xpsampling = np.genfromtxt(file_name, skip_header=1, delimiter=',', dtype=float)
    n_wl = int(_xpsampling.shape[0] / 2)

    bp_sampling = _xpsampling[:n_wl, :]
    bp_sampling = np.transpose(bp_sampling)

    rp_sampling = _xpsampling[n_wl:, :]
    rp_sampling = np.transpose(rp_sampling)

    xpsampling = dict(zip(BANDS, [bp_sampling, rp_sampling]))
    return xpsampling
