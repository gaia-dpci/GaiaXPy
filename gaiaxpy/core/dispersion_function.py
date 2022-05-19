"""
dispersion_function.py
====================================
Module providing utilities to convert pseudo-wavelength to absolute wavelength and viceversa.
"""

import numpy as np
import pandas as pd
from configparser import ConfigParser
from functools import lru_cache
from scipy import interpolate
from os.path import join
from gaiaxpy.config import config_path
from gaiaxpy.core.satellite import BANDS, BP_WL, RP_WL


@lru_cache(maxsize=None)
def read_config_file():
    config_parser = ConfigParser()
    config_parser.read(join(config_path, 'config.ini'))
    config_file = join(config_path, config_parser.get('core', 'dispersion_function'))
    return pd.read_csv(config_file)


@lru_cache(maxsize=None)
def generate_bp_conversion():
    df = read_config_file()
    wl = df['wl_nm'].copy()
    pwl = df['bp_pwl'].copy()
    flipped_pwl = np.flipud(df['bp_pwl'].copy())
    flipped_wl = np.flipud(df['wl_nm'].copy())
    bp_pwl_to_wl = interpolate.interp1d(flipped_pwl, flipped_wl, kind='linear', bounds_error=False, fill_value='extrapolate')
    bp_wl_to_pwl = interpolate.interp1d(wl, pwl, kind='linear', bounds_error=False, fill_value='extrapolate')
    return bp_pwl_to_wl, bp_wl_to_pwl


@lru_cache(maxsize=None)
def generate_rp_conversion():
    df = read_config_file()
    df_not_nan = df[df['rp_pwl'].notna()]
    wl = df_not_nan['wl_nm'].copy()
    pwl = df_not_nan['rp_pwl'].copy()
    rp_pwl_to_wl = interpolate.interp1d(pwl, wl, kind='linear', bounds_error=False, fill_value='extrapolate')
    rp_wl_to_pwl = interpolate.interp1d(wl, pwl, kind='linear', bounds_error=False, fill_value='extrapolate')
    return rp_pwl_to_wl, rp_wl_to_pwl


bp_pwl_to_wl, bp_wl_to_pwl = generate_bp_conversion()
bp_pwl_range = [bp_wl_to_pwl(BP_WL.low), bp_wl_to_pwl(BP_WL.high)]
bp_wl_range = [BP_WL.low, BP_WL.high]


rp_pwl_to_wl, rp_wl_to_pwl = generate_rp_conversion()
rp_pwl_range = [rp_wl_to_pwl(RP_WL.low), rp_wl_to_pwl(RP_WL.high)]
rp_wl_range = [RP_WL.low, RP_WL.high]


def pwl_to_wl(band, pwl):
    """
    Convert the input pseudo-wavelength value(s) into absolute wavelength for the input
    band (BP or RP).

    Args:
        band (str): BP or RP.
        pwl (ndarray): 1D array containing the pseudo-wavelengths to be converted.

    Returns:
        (ndarray): The absolute wavelengths corresponding to the input pseudo-wavelength values.

    Raises:
        ValueError: If the band string is not equal to BP or RP.
    """
    if band.lower() == BANDS.bp:
        return bp_pwl_to_wl(pwl)
    elif band.lower() == BANDS.rp:
        return rp_pwl_to_wl(pwl)
    else:
        raise ValueError("Unrecognised input band. Only 'BP' or 'RP' values are recognised.")


def wl_to_pwl(band, wl):
    """
    Convert the input wavelength value(s) into pseudo-wavelength for the input
    band (BP or RP).

    Args:
        band (str): BP or RP.
        wl (ndarray): 1D array containing the absolute wavelengths to be converted.

    Returns:
        (ndarray): The pseudo-wavelengths corresponding to the input absolute wavelength values.

    Raises:
        ValueError: If the band string is not equal to BP or RP.
    """
    if band.lower() == BANDS.bp:
        return bp_wl_to_pwl(wl)
    elif band.lower() == BANDS.rp:
        return rp_wl_to_pwl(wl)
    else:
        raise ValueError("Unrecognised input band. Only 'BP' or 'RP' values are recognised.")


def pwl_range(band):
    '''
    Return the range where the dispersion function is interpolated. Outside this range extrapolation will occur.

    Args:
        band (str): BP or RP.

    Returns:
        (list): The minimum and maximum values of the pseudo-wavelength range.

    Raises:
        ValueError: If the band string is not equal to BP or RP.
    '''
    if band.lower() == BANDS.bp:
        return bp_pwl_range
    elif band.lower() == BANDS.rp:
        return rp_pwl_range
    else:
        raise ValueError("Unrecognised input band. Only 'BP' or 'RP' values are recognised.")


def wl_range(band):
    '''
    Return the range where the dispersion function is interpolated. Outside this range extrapolation will occur.

    Args:
        band (str): BP or RP.

    Returns:
        (list): The minimum and maximum values of the wavelength range.

    Raises:
        ValueError: If the band string is not equal to BP or RP.
    '''
    if band.lower() == BANDS.bp:
        return bp_wl_range
    elif band.lower() == BANDS.rp:
        return rp_wl_range
    else:
        raise ValueError("Unrecognised input band. Only 'BP' or 'RP' values are recognised.")
