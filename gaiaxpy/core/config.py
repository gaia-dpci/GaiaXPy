"""
config.py
====================================
Module to handle the calibrator and generator configuration files.
"""

from configparser import ConfigParser
from os.path import join

from gaiaxpy.config.paths import config_path, filters_path
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.core.xml_utils import get_file_root, get_array_text, get_xp_merge, get_xp_sampling_matrix

ADDITIONAL_SYSTEM_PREFIX = 'USER'


def get_file_path(config_file=None):
    if not config_file:
        return filters_path
    _config_parser = ConfigParser()
    _config_parser.read(config_file)
    try:
        file_path = _config_parser['filter']['filters_dir']
    except KeyError:
        return filters_path
    return file_path


def get_filter_version_from_config(_config_parser):
    # TODO: return built-in version if the version section is not found.
    try:
        version = _config_parser['filter']['version']
    except KeyError:
        version = None
    return version


def replace_file_name(_config_file, label, key, bp_model, rp_model, system):
    _config_parser = ConfigParser()
    _config_parser.read(_config_file)
    version = get_filter_version_from_config(_config_parser)
    if version:
        file_name = _config_parser.get(label, key).replace('version', version)
        system = system.replace(f'{ADDITIONAL_SYSTEM_PREFIX}_', '')
    else:
        file_name = _config_parser.get(label, key).format(label, key).replace('model', f'{bp_model}{rp_model}')
    file_name = file_name.replace('system', system) if system else file_name.replace('system_', '')
    return file_name


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
    _config_file = join(config_path, 'config.ini') if config_file is None else config_file
    file_name = replace_file_name(_config_file, label, key, bp_model, rp_model, system)
    file_path = get_file_path(config_file)
    return join(file_path, file_name)


def _load_xpmerge_from_xml(system=None, bp_model=None, rp_model='v142r', config_file=None):
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
    file_path = get_file(label, key, system, bp_model, rp_model, config_file=config_file)
    x_root = get_file_root(file_path)
    sampling_grid, bp_merge, rp_merge = get_xp_merge(x_root)
    return sampling_grid, dict(zip(BANDS, [bp_merge, rp_merge]))


def _load_xpsampling_from_xml(system=None, bp_model=None, rp_model='v142r', config_file=None):
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
    xml_file = get_file('filter', 'filter', system, bp_model, rp_model, config_file=config_file)
    x_root = get_file_root(xml_file)
    _, nbands = get_array_text(x_root, 'bands')

    bp_sampling = get_xp_sampling_matrix(x_root, 'bp', nbands)
    rp_sampling = get_xp_sampling_matrix(x_root, 'rp', nbands)

    xp_sampling = dict(zip(BANDS, [bp_sampling, rp_sampling]))
    return xp_sampling
