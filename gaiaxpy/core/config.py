"""
config.py
====================================
Module to handle the calibrator and generator configuration files.
"""

from configparser import ConfigParser
from os.path import join

from gaiaxpy.config.paths import config_path, filters_path
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.core.xml_utils import get_file_root, parse_array, get_array_text, get_xp_merge, get_xp_sampling_matrix


_ADDITIONAL_SYSTEM_PREFIX = 'USER'

def get_file(label, key, system, bp_model, rp_model, config_file=None):
    """
    Get the file path corresponding to the given label and key.

    Args:
        label (str): Label of the photometric system or functionality (e.g.: 'Johnson' or 'calibrator').
        key (str): Type of file to load ('zeropoint', 'merge', 'sampling').
        system (str): Photometric system name, can be None in which case the generic configuration is loaded.
        bp_model (str): BP model.
        rp_model (str): RP model.
        config_file: Path to configuration file.

    Returns:
        str: Path of a file.
    """
    config_file = join(config_path, 'config.ini') if not config_file else config_file
    _config_parser = ConfigParser()
    _config_parser.read(config_file)
    file_name = _config_parser.get(label, key).format(label, key).replace('model', f'{bp_model}{rp_model}')
    file_name = file_name.replace('system', system) if system else file_name.replace('system_', '')
    return join(filters_path, file_name)


def _load_offset_from_xml(system, bp_model='v375wi', rp_model='v142r'):
    """
    Load the offset of a standard photometric system from the filter XML file.

    Args:
        system (str): Photometric system name.
        bp_model (str): BP model.
        rp_model (str): RP model.

    Returns:
        ndarray: Array of offsets.
    """
    label = key = 'filter'
    file_path = get_file(label, key, system, bp_model, rp_model)
    x_root = get_file_root(file_path)
    return parse_array(x_root, 'fluxBias')


def _load_xpzeropoint_from_xml(system, bp_model='v375wi', rp_model='v142r', config_file=None):
    """
    Load the zero-points for each band from the filter XML file.

    Args:
        system (str): Name of the photometric system.
        bp_model (str): BP model.
        rp_model (str): RP model.
        config_file (str): Path to configuration file.

    Returns:
        ndarray: Array of zero-points.
    """
    label = key = 'filter'
    file_path = get_file(label, key, system, bp_model, rp_model, config_file=config_file)
    x_root = get_file_root(file_path)
    zeropoints = parse_array(x_root, 'zeropoints')
    bands, _ = get_array_text(x_root, 'bands')
    return bands, zeropoints


def _load_xpmerge_from_xml(system=None, bp_model=None, rp_model='v142r'):
    """
    Load the XpMerge table from the filter XML file.

    Args:
        system (str): Name of the photometric system if it corresponds.
        bp_model (str): BP model.
        rp_model (str): RP model.

    Returns:
        ndarray: Array containing the sampling grid values.
        dict: A dictionary containing the XpMerge table with one entry for BP and one for RP.
    """
    bp_model = bp_model if bp_model else 'v375wi'
    label = key = 'filter'
    file_path = get_file(label, key, system, bp_model, rp_model)
    x_root = get_file_root(file_path)
    sampling_grid, bp_merge, rp_merge = get_xp_merge(x_root)
    return sampling_grid, dict(zip(BANDS, [bp_merge, rp_merge]))


def _load_xpsampling_from_xml(system=None, bp_model=None, rp_model='v142r'):
    """
    Load the XpSampling table from the XML filter file.

    Args:
        system (str): Photometric system name, can be None in which case the generic configuration is loaded.
        bp_model (str): BP model.
        rp_model (str): RP model.

    Returns:
        dict: A dictionary containing the XpSampling table with one entry for BP and one for RP.
    """
    bp_model = bp_model if bp_model else 'v375wi'
    xml_file = get_file('filter', 'filter', system, bp_model, rp_model)
    x_root = get_file_root(xml_file)
    _, nbands = get_array_text(x_root, 'bands')

    bp_sampling = get_xp_sampling_matrix(x_root, 'bp', nbands)
    rp_sampling = get_xp_sampling_matrix(x_root, 'rp', nbands)

    xp_sampling = dict(zip(BANDS, [bp_sampling, rp_sampling]))
    return xp_sampling
