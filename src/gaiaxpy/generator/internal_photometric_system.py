"""
internal_photometric_system.py
====================================
Module for the parent class of the standardised and regular photometric systems.
"""
import re
from configparser import ConfigParser
from glob import glob
from os import remove
from os.path import exists, split, join

from gaiaxpy.core.version import __version__
from gaiaxpy.config.paths import config_ini_file
from gaiaxpy.core.config import (get_filter_version_from_config, replace_file_name, get_file_path,
                                 ADDITIONAL_SYSTEM_PREFIX)
from gaiaxpy.core.generic_functions import _get_system_label
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.core.xml_utils import get_file_root, parse_array, get_array_text, get_xp_sampling_matrix, get_xp_merge
from .config import _CFG_FILE_PATH, _ADDITIONAL_SYSTEM_FILES_REGEX


class InternalPhotometricSystem(object):

    def __init__(self, name: str, config_file: str = None, bp_model: str = 'v375wi', rp_model: str = 'v142r'):
        self.label = _get_system_label(name)
        self.version = None
        self.__set_version(config_file)
        config_file = config_ini_file if not config_file else config_file
        self.config_file = config_file
        self.filter_file = None
        self._set_file(bp_model=bp_model, rp_model=rp_model)
        self.bands = None
        self.zero_points = None
        self._load_xpzeropoint_from_xml()
        self.offsets = None
        self._load_offset_from_xml()
        self.name = name

    def set_bands(self, bands):
        """
        Set the bands of the photometric system.

        Args:
            bands (list): List of bands in this photometric system.
        """
        self.bands = list(bands)

    def get_bands(self):
        """
        Get the bands of the photometric system.

        Returns:
            list of str: List of bands.
        """
        return self.bands

    def set_offsets(self, offsets):
        self.offsets = offsets

    def get_offsets(self):
        return self.offsets

    def get_system_label(self):
        """
        Get the label of the photometric system.

        Returns:
            str: A short description of the photometric system.
        """
        return self.label

    def set_zero_points(self, zero_points):
        """
        Set the zero-points needed to convert the Gaia fluxes in the bands defining this photometric system to
            magnitudes.

        Args:
            zero_points (nparray): 1D array containing the zero-point for each of the bands in this photometric system.
        """
        self.zero_points = zero_points

    def __set_version(self, config_file):
        if not config_file:
            self.version = __version__
        else:
            _config_parser = ConfigParser()
            _config_parser.read(config_file)
            self.version = get_filter_version_from_config(_config_parser)

    def get_zero_points(self):
        """
        Get the zero-points of the photometric system.

        Returns:
            ndarray: 1D array containing the zero-points for all bands in
            this photometric system.
        """
        return self.zero_points

    def _correct_flux(self, flux):
        raise ValueError('Method not implemented in parent class.')

    def _correct_error(self, flux, error):
        raise ValueError('Method not implemented in parent class.')

    def _set_file(self, bp_model, rp_model):
        """
        Get the file path corresponding to the given label and key.

        Args:
            bp_model (str): BP model.
            rp_model (str): RP model.

        Returns:
            str: Path of a file.
        """

        def _extract_matches(_actual_path, _system_name):
            __is_built_in_name = lambda fname: fname.startswith('XpFilter')
            __is_exact_match = lambda fname, sysname: fname.startswith(sysname) and f'{sysname}.' in fname
            __matches_additional = lambda fname: pattern.match(fname)
            __split_paths = [split(p) for p in _actual_path]
            __paths, __filenames = zip(*__split_paths)
            pattern = re.compile(_ADDITIONAL_SYSTEM_FILES_REGEX, re.IGNORECASE)
            if all(__is_built_in_name(f) for f in __filenames):  # If system is built-in
                return _actual_path
            return [join(p, fn) for p, fn in __split_paths if not __is_built_in_name(fn) and __matches_additional(fn)
                    and __is_exact_match(fn, _system_name)]  # If is additional

        def _validate_path(_actual_path):
            if len(actual_path) == 0:
                raise ValueError('Filter file not found in given path.')
            elif len(actual_path) > 1:
                # Remove configuration file if it exists to avoid issues when reloading
                if exists(_CFG_FILE_PATH):
                    remove(_CFG_FILE_PATH)
                raise ValueError(f'More than one system named {self.label.replace(f"{ADDITIONAL_SYSTEM_PREFIX}_", "")}'
                                 f' were found. System names in the given directory should be unique. Operation aborted.')

        file_name = replace_file_name(self.config_file, 'filter', 'filter', bp_model, rp_model, self.label)
        system_name = file_name.split('.')[0]
        file_path = get_file_path(self.config_file)
        # Search file in file path to obtain the actual path
        actual_path = glob(file_path + f"/**/{system_name}*.xml", recursive=True)
        actual_path = _extract_matches(actual_path, system_name)
        _validate_path(actual_path)
        self.filter_file = actual_path[0]

    def _load_offset_from_xml(self):
        """
        Load the offset of a standard photometric system from the filter XML file.

        Returns:
            ndarray: Array of offsets.
        """
        x_root = get_file_root(self.filter_file)
        self.offsets = parse_array(x_root, 'fluxBias')

    def _load_xpzeropoint_from_xml(self):
        """
        Load the zero-points for each band from the filter XML file.

        Returns:
            ndarray: Array of zero-points.
        """
        x_root = get_file_root(self.filter_file)
        self.zero_points = parse_array(x_root, 'zeropoints')
        self.bands, _ = get_array_text(x_root, 'bands')

    def load_xpsampling_from_xml(self):
        """
        Load the XpSampling table from the XML filter file.

        Returns:
            dict: A dictionary containing the XpSampling table with one entry for BP and one for RP.
        """
        x_root = get_file_root(self.filter_file)
        _, n_bands = get_array_text(x_root, 'bands')

        bp_sampling = get_xp_sampling_matrix(x_root, 'bp', n_bands)
        rp_sampling = get_xp_sampling_matrix(x_root, 'rp', n_bands)

        xp_sampling = dict(zip(BANDS, [bp_sampling, rp_sampling]))
        return xp_sampling

    def load_xpmerge_from_xml(self):
        """
        Load the XpMerge table from the filter XML file.

        Returns:
            ndarray: Array containing the sampling grid values.
            dict: A dictionary containing the XpMerge table with one entry for BP and one for RP.
        """
        x_root = get_file_root(self.filter_file)
        sampling_grid, bp_merge, rp_merge = get_xp_merge(x_root)
        return sampling_grid, dict(zip(BANDS, [bp_merge, rp_merge]))
