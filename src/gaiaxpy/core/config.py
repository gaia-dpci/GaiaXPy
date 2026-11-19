"""
config.py
====================================
Module to handle the calibrator and generator configuration files.
"""
from pathlib import Path
from typing import Union

import numpy as np
import yaml

from gaiaxpy.core.generic_variables import YAML_EXTENSIONS
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.core.utils import get_file_root, get_array_text, get_xp_merge, get_xp_sampling_matrix


def _is_yaml_file(file_path: Union[Path, str]) -> bool:
    return str(file_path).lower().endswith(YAML_EXTENSIONS)


def _load_yaml_config(xp_filter_file: Union[Path, str]) -> dict:
    xp_filter_file = Path(xp_filter_file)

    if not xp_filter_file.is_file():
        raise FileNotFoundError(f'File not found: {xp_filter_file}')

    with xp_filter_file.open('r', encoding='utf-8') as yaml_file:
        yaml_root = yaml.safe_load(yaml_file)

    return yaml_root.get('config', yaml_root)


def _get_yaml_array(xp_filter_file: Union[Path, str], yaml_config: dict, array_config) -> \
        'np.ndarray':
    """
    Load an array stored in a YAML (with an array or an index to a NPZ file) or a NPZ file.
    """
    import numpy as np

    if isinstance(array_config, dict):
        if 'values' in array_config:
            return np.asarray(array_config['values'], dtype=float)

        if 'npz_key' in array_config:
            array_file = yaml_config.get('arrayFile')

            if not array_file:
                raise ValueError('The YAML configuration contains an npz_key but does not '
                                 'define config.arrayFile.')

            npz_path = Path(xp_filter_file).parent / array_file

            if not npz_path.is_file():
                raise FileNotFoundError(f'NPZ resource file not found: {npz_path}')

            npz_key = array_config['npz_key']

            with np.load(npz_path, allow_pickle=False) as npz_file:
                if npz_key not in npz_file:
                    raise KeyError(f'Array {npz_key!r} not found in {npz_path}. '
                                   f'Available arrays: {npz_file.files}')

                return np.asarray(npz_file[npz_key], dtype=float)

        raise ValueError("Array configuration must contain either 'values' or 'npz_key'.")

    # Backwards compatibility for arrays written directly as YAML lists.
    return np.asarray(array_config, dtype=float)


def load_xpmerge_from_yaml(xp_filter_file: Union[Path, str]) -> ('np.ndarray', dict):
    """
    Load the XpMerge table from the filter YAML file.
    """
    yaml_config = _load_yaml_config(xp_filter_file)
    xp_merge_config = yaml_config['XpMerge']

    sampling_grid = _get_yaml_array(xp_filter_file, yaml_config,
                                    xp_merge_config['sampleMeanWavelengths'])
    bp_merge = _get_yaml_array(xp_filter_file, yaml_config, xp_merge_config['bpWeights'])
    rp_merge = _get_yaml_array(xp_filter_file, yaml_config, xp_merge_config['rpWeights'])

    return sampling_grid, dict(zip(BANDS, [bp_merge, rp_merge]))


def load_xpmerge_from_npz(xp_filter_file: Union[Path, str]) -> ('np.ndarray', dict):
    sampling_grid = _load_npz_array(xp_filter_file,
                                    'config/XpMerge/sampleMeanWavelengths').astype(float, copy=False)

    bp_merge = _load_npz_array(xp_filter_file, 'config/XpMerge/bpWeights').astype(float, copy=False)
    rp_merge = _load_npz_array(xp_filter_file, 'config/XpMerge/rpWeights').astype(float, copy=False)

    return sampling_grid, dict(zip(BANDS, [bp_merge, rp_merge]))


def load_xpmerge_from_file(xp_filter_file: Union[Path, str]) -> ('np.ndarray', dict):
    """
    Load the XpMerge table from the filter XML or YAML file.

    Args:
        xp_filter_file: Path to the XpFilter file.

    Returns:
        Array containing the sampling grid values and a dictionary containing
        the XpMerge table for BP and RP.
    """
    if _is_npz_file(xp_filter_file):
        return load_xpmerge_from_npz(xp_filter_file)

    if _is_yaml_file(xp_filter_file):
        return load_xpmerge_from_yaml(xp_filter_file)

    x_root = get_file_root(xp_filter_file)
    sampling_grid, bp_merge, rp_merge = get_xp_merge(x_root)

    return sampling_grid, dict(zip(BANDS, [bp_merge, rp_merge]))


def _is_npz_file(file_path: Union[Path, str]) -> bool:
    return str(file_path).lower().endswith('.npz')


def _load_npz_array(npz_file: Union[Path, str], key: str) -> 'np.ndarray':
    npz_file = Path(npz_file)

    if not npz_file.is_file():
        raise FileNotFoundError(f'File not found: {npz_file}')

    with np.load(npz_file, allow_pickle=False) as archive:
        if key not in archive:
            raise KeyError(f'Array {key!r} not found in {npz_file}. '
                           f'Available arrays: {archive.files}')

        return np.asarray(archive[key])


def _load_xp_sampling_matrix_from_npz(xp_filter_file: Union[Path, str], xp: str) -> 'np.ndarray':
    prefix = f'config/XpSampling/{xp.lower()}SampledBases'

    values = _load_npz_array(xp_filter_file, prefix).astype(float, copy=False)
    sampling_grid = _load_npz_array(xp_filter_file, 'config/XpMerge/sampleMeanWavelengths')

    n_samples = sampling_grid.size

    if values.size % n_samples:
        raise ValueError(f'Invalid {xp.upper()} sampling matrix: '
                         f'{values.size} values cannot be divided into '
                         f'{n_samples} wavelength samples.')

    dimension = values.size // n_samples

    return values.reshape(n_samples, dimension).T


def load_xpsampling_from_npz(xp_filter_file: Union[Path, str]) -> dict:
    bp_sampling = _load_xp_sampling_matrix_from_npz(xp_filter_file, BANDS.bp)
    rp_sampling = _load_xp_sampling_matrix_from_npz(xp_filter_file, BANDS.rp)

    if bp_sampling.shape[1] != rp_sampling.shape[1]:
        raise ValueError('BP and RP sampling matrices contain different numbers '
                         f'of samples: {bp_sampling.shape[1]} and {rp_sampling.shape[1]}.')

    return dict(zip(BANDS, [bp_sampling, rp_sampling]))


def load_xpsampling_from_yaml(xp_filter_file: Union[Path, str]) -> dict:
    """
    Load the XpSampling table from the filter YAML file.
    """
    yaml_config = _load_yaml_config(xp_filter_file)
    xp_sampling = yaml_config["XpSampling"]

    output = {}

    for band in BANDS:
        cfg = xp_sampling[f"{band}SampledBases"]

        values = np.asarray(cfg["values"], dtype=float)
        dimension = cfg["dimension"]

        output[band] = values.reshape(-1, dimension).T

    return output


def load_xpsampling_from_file(xp_filter_file: Union[Path, str]) -> dict:
    """
    Load the XpSampling table from the XML or YAML filter file.

    Args:
        xp_filter_file: Path to the XpFilter file.

    Returns:
        Dictionary containing the XpSampling table for BP and RP.
    """
    if _is_npz_file(xp_filter_file):
        return load_xpsampling_from_npz(xp_filter_file)

    if _is_yaml_file(xp_filter_file):
        return load_xpsampling_from_yaml(xp_filter_file)

    x_root = get_file_root(xp_filter_file)
    _, n_bands = get_array_text(x_root, 'bands')

    bp_sampling = get_xp_sampling_matrix(x_root, BANDS.bp, n_bands)
    rp_sampling = get_xp_sampling_matrix(x_root, BANDS.rp, n_bands)

    return dict(zip(BANDS, [bp_sampling, rp_sampling]))
