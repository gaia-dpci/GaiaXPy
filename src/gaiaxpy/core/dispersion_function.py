"""Convert between XP pseudo-wavelength coordinates and wavelength in nm.

The conversion uses release-specific tabulated dispersion files distributed
with GaiaXPy. BP and RP each have forward and inverse linear interpolators;
values outside the tabulated coordinate bounds are linearly extrapolated.

The table and interpolators are cached in memory. The range helpers report the
configured BP/RP wavelength endpoints and their converted coordinates. Those
endpoints are separate from the complete bounds of the tabulated data.
Configuration versions and references are available through read_config_metadata
in core.config_metadata; the conversion functions return coordinates only.
"""

from functools import lru_cache
from os.path import join

import numpy as np
import pandas as pd
from scipy import interpolate

from gaiaxpy.config.paths import config_path
from gaiaxpy.core.config_dispatcher import Config
from gaiaxpy.core.generic_functions import parse_band
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.core.release_resolution import parse_release
from gaiaxpy.core.satellite import BANDS, BP_WL_DR3, RP_WL_DR3


@lru_cache(maxsize=None)
def read_config_file(release):
    """Read and cache the dispersion table selected for a release.

    Args:
        release (str): Gaia release label, 'dr3', ignoring case.

    Returns:
        pandas.DataFrame: Table with wl_nm, bp_pwl and rp_pwl columns. The cached
        DataFrame is returned directly, without copying.

    Raises:
        InvalidReleaseError: A supplied release label is unrecognised.

    Notes:
        The filename is selected through config.yaml. CSV comment lines are
        skipped and floating-point text is read with round-trip precision.
        A concrete release is required; None has no table configuration.
        File and CSV-reader errors are passed back to the caller. Callers should
        not mutate the shared cached table.
    """
    release = parse_release(release)
    config = Config().get()['core']
    _path = config[release]['path']
    filename = config[release]['dispersion_function']
    return pd.read_csv(join(config_path, _path, filename), comment='#', **CSV_FLOAT_PRECISION_KWARGS)


__WL_RANGES = {
    RELEASES.dr3: {BANDS.bp: BP_WL_DR3, BANDS.rp: RP_WL_DR3}
}


@lru_cache(maxsize=None)
def generate_bp_conversion(release):
    """Build and cache the two linear BP coordinate conversions for a release.

    Args:
        release (str): Dispersion-table release.

    Returns:
        tuple: SciPy interp1d objects for pseudo-wavelength to wavelength in nm,
        followed by wavelength in nm to pseudo-wavelength.

    Notes:
        The BP columns are copied from the table. They are reversed for the
        pseudo-wavelength-to-wavelength interpolator. Both interpolators use
        linear extrapolation outside their input-coordinate bounds.
    """
    df = read_config_file(release)
    wl = df['wl_nm'].copy()
    pwl = df['bp_pwl'].copy()
    flipped_pwl = np.flipud(df['bp_pwl'].copy())
    flipped_wl = np.flipud(df['wl_nm'].copy())
    bp_pwl_to_wl = interpolate.interp1d(flipped_pwl, flipped_wl, kind='linear', bounds_error=False,
                                        fill_value='extrapolate')
    bp_wl_to_pwl = interpolate.interp1d(wl, pwl, kind='linear', bounds_error=False, fill_value='extrapolate')
    return bp_pwl_to_wl, bp_wl_to_pwl


@lru_cache(maxsize=None)
def generate_rp_conversion(release):
    """Build and cache the two linear RP coordinate conversions for a release.

    Args:
        release (str): Dispersion-table release.

    Returns:
        tuple: SciPy interp1d objects for pseudo-wavelength to wavelength in nm,
        followed by wavelength in nm to pseudo-wavelength.

    Notes:
        Rows with missing rp_pwl values are excluded before building the
        interpolators. Both use linear extrapolation outside their coordinate
        bounds.
    """
    df = read_config_file(release)
    df_not_nan = df[df['rp_pwl'].notna()]
    wl = df_not_nan['wl_nm'].copy()
    pwl = df_not_nan['rp_pwl'].copy()
    rp_pwl_to_wl = interpolate.interp1d(pwl, wl, kind='linear', bounds_error=False, fill_value='extrapolate')
    rp_wl_to_pwl = interpolate.interp1d(wl, pwl, kind='linear', bounds_error=False, fill_value='extrapolate')
    return rp_pwl_to_wl, rp_wl_to_pwl


@lru_cache(maxsize=None)
def _get_conversions(release):
    """Return the cached BP/RP forward and inverse interpolators for a release.

    The release is normalised with parse_release. The nested mapping is keyed
    first by bp/rp, then by pwl_to_wl/wl_to_pwl. It is returned without copying.
    """
    release = parse_release(release)
    bp_pwl_to_wl, bp_wl_to_pwl = generate_bp_conversion(release)
    rp_pwl_to_wl, rp_wl_to_pwl = generate_rp_conversion(release)
    return {
        BANDS.bp: {
            'pwl_to_wl': bp_pwl_to_wl,
            'wl_to_pwl': bp_wl_to_pwl,
        },
        BANDS.rp: {
            'pwl_to_wl': rp_pwl_to_wl,
            'wl_to_pwl': rp_wl_to_pwl,
        },
    }


def pwl_to_wl(band, pwl, release):
    """Convert XP pseudo-wavelength coordinates to wavelength in nm.

    Args:
        band (str): BP or RP; case is ignored. A one-element string list is
            also accepted by the shared band parser.
        pwl (float, list or numpy.ndarray): Coordinate or coordinates to convert.
        release (str): Gaia release selecting the tabulated dispersion relation: 'dr3', ignoring case.

    Returns:
        float or numpy.ndarray: Wavelength in nm. Scalar input gives a Python
        float; list/array input gives an array with the corresponding shape.

    Raises:
        InvalidBandError: The photometer label is unrecognised.
        InvalidReleaseError: The release label is unrecognised.

    Notes:
        The conversion is piecewise linear in the supplied table. Outside its
        tabulated pseudo-wavelength bounds, linear extrapolation is used rather
        than an out-of-range error. The configured ranges reported by wl_range
        and pwl_range are not enforced by this function.
    """
    band = parse_band(band)
    release = parse_release(release)
    result = _get_conversions(release)[band]['pwl_to_wl'](pwl)
    return result.item() if np.ndim(result) == 0 else result


def wl_to_pwl(band, wl, release):
    """Convert wavelength in nm to XP pseudo-wavelength coordinates.

    Args:
        band (str): BP or RP, ignoring case. A one-element string list is also
            accepted by the shared band parser.
        wl (float, list or numpy.ndarray): Wavelength or wavelengths in nm.
        release (str): Gaia release selecting the tabulated dispersion relation: 'dr3', ignoring case.

    Returns:
        float or numpy.ndarray: Pseudo-wavelength coordinates. Scalar input
        gives a Python float; list/array input gives an array with the
        corresponding shape.

    Raises:
        InvalidBandError: The photometer label is unrecognised.
        InvalidReleaseError: The release label is unrecognised.

    Notes:
        The conversion is piecewise linear in the supplied table. Outside its
        tabulated wavelength bounds, linear extrapolation is used rather than
        an out-of-range error. The configured BP/RP wavelength ranges are not
        enforced here.
    """
    band = parse_band(band)
    release = parse_release(release)
    result = _get_conversions(release)[band]['wl_to_pwl'](wl)
    return result.item() if np.ndim(result) == 0 else result


def pwl_range(band, release):
    """Convert the configured wavelength endpoints to pseudo-wavelength coordinates.

    Args:
        band (str): BP or RP, ignoring case.
        release (str): 'dr3', ignoring case.

    Returns:
        list[float]: Two coordinates, corresponding first to the configured low
        wavelength and then to the high wavelength. The result is not sorted;
        for BP it is descending because the dispersion relation is reversed.

    Raises:
        InvalidBandError: The photometer label is unrecognised.
        InvalidReleaseError: The release label is unrecognised.

    Notes:
        These endpoints come from the release-specific constants in satellite.py,
        not from the minimum and maximum coordinates of the interpolation table.
        The helper does not apply limits to later conversion calls.
    """
    band = parse_band(band)
    release = parse_release(release)
    wl = __WL_RANGES[release][band]
    wl_to_pwl_func = _get_conversions(release)[band]['wl_to_pwl']
    return [float(wl_to_pwl_func(wl.low)), float(wl_to_pwl_func(wl.high))]


def wl_range(band, release):
    """Return the configured wavelength endpoints for a photometer and release.

    Args:
        band (str): BP or RP, ignoring case.
        release (str): 'dr3', ignoring case.

    Returns:
        WLRange: Named tuple with low and high wavelength endpoints in nm,
        taken from the release-specific constants in satellite.py.

    Raises:
        InvalidBandError: The photometer label is unrecognised.
        InvalidReleaseError: The release label is unrecognised.

    Notes:
        This reads constants without loading the dispersion table. These are
        configured BP/RP endpoints, not the complete bounds of the tabulated
        dispersion relation. Conversions are not restricted to this range.
    """
    band = parse_band(band)
    release = parse_release(release)
    return __WL_RANGES[release][band]
