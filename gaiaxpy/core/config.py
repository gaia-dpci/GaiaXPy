"""
config.py
====================================
Module to handle the calibrator and generator configuration files.
"""

import numpy as np
from configparser import ConfigParser
from numbers import Number
from os import path
from gaiaxpy.config import config_path, filters_path
from gaiaxpy.core.satellite import BANDS

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))


def get_file(label, key, system, bp_model, rp_model):
    """
    Get the file path corresponding to the given label and key.

    Args:
        label (str): Label of the photometric system or functionality (e.g.: 'Johnson' or 'calibrator').
        key (str): Type of file to load ('zeropoint', 'merge', 'sampling').

    Returns:
        str: Path of a file.
    """
    filter_config_file_path = path.join(filters_path, config_parser.get(label, key))
    generic_file_name = filter_config_file_path.format(label, key).replace('model', f'{bp_model}{rp_model}')
    if system:
        # Split path and get only the file name
        head, tail = path.split(generic_file_name)
        tail = tail.replace('system', system)
        # Rejoin modified path
        generic_file_name = path.join(head, tail)
    return generic_file_name


def _load_offset_from_csv(system, label = 'photsystem', bp_model='v375wi', rp_model='v142r'):
    """
    Load the offset of a standard photometric system.
    """
    file_path = get_file(label, 'offset', system, bp_model, rp_model)
    try:
        offset = np.genfromtxt(file_path, delimiter=',', dtype=float)
    except OSError:
         raise ValueError('Offset file not present. Is this a standard system?')
    return offset


def _load_xpzeropoint_from_csv(system, label='photsystem', bp_model='v375wi',
                               rp_model='v142r'):
    """
    Load the zero-points for each band.

    Args:
        label (str): Label of the photometric system or functionality.

    Returns:
        ndarray: Loaded zero-points from the CSV file.
    """
    def _make_iterable(variable):
        if isinstance(variable, str):
            return np.array([variable])
        return variable
    bands, zero_points =  np.genfromtxt(
            get_file(label, 'zeropoint', system, bp_model, rp_model),
            delimiter=',', dtype=str)
    bands = _make_iterable(bands).astype(str)
    zero_points = _make_iterable(zero_points).astype(float)
    return bands, zero_points


def _load_xpmerge_from_csv(
        label,
        system=None,
        bp_model=None,
        rp_model='v142r'):
    """
    Load the XpMerge table as provided by PMN in CSV.

    Args:
        label (str): Label of the photometric system or functionality.

    Returns:
        ndarray: Array containing the samplig grid values.
        dict: A dictionary containing the XpMerge table with one entry for BP and one for RP.
    """
    def _parse_merge(_xpmerge):
        # np.genfromtxt can only return numbers and NumPy arrays.
        if isinstance(_xpmerge[0], Number):
            # Make iterable
            _xpmerge = [np.array([element]) for element in _xpmerge]
            sampling_grid = _xpmerge[0]
            bp_merge = _xpmerge[1]
            rp_merge = _xpmerge[2]
        else:
            sampling_grid = _xpmerge[0, :]
            bp_merge = _xpmerge[1, :]
            rp_merge = _xpmerge[2, :]
        return sampling_grid, bp_merge, rp_merge
    if not bp_model:
        bp_model = 'v375wi'
    file_name = get_file(label, 'merge', system, bp_model, rp_model)
    _xpmerge = np.genfromtxt(
        file_name,
        skip_header=1,
        delimiter=',',
        dtype=float)
    sampling_grid, bp_merge, rp_merge = _parse_merge(_xpmerge)
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
    _xpsampling = np.genfromtxt(
        file_name,
        skip_header=1,
        delimiter=',',
        dtype=float)
    n_wl = int(_xpsampling.shape[0] / 2)

    bp_sampling = _xpsampling[:n_wl, :]
    bp_sampling = np.transpose(bp_sampling)

    rp_sampling = _xpsampling[n_wl:, :]
    rp_sampling = np.transpose(rp_sampling)

    xpsampling = dict(zip(BANDS, [bp_sampling, rp_sampling]))
    return xpsampling
