"""
internal_photometric_system.py
====================================
Module for the parent class of the standardised and regular photometric systems.
"""
from glob import glob
from os.path import join

from gaiaxpy.config.paths import config_path
from gaiaxpy.core.config import replace_file_name, get_file_path
from gaiaxpy.core.xml_utils import get_array_text, get_file_root, parse_array, get_xp_sampling_matrix, get_xp_merge
from ..core.generic_functions import _get_system_label
from ..core.satellite import BANDS


class InternalPhotometricSystem(object):

    def __init__(self, name, config_file=None, bp_model='v375wi', rp_model='v142r'):
        self.label = _get_system_label(name)
        config_file = join(config_path, 'config.ini') if not config_file else config_file
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
        Set the zero-points needed to convert the Gaia fluxes in the
        bands defining this photometric system to magnitudes.

        Args:
            zero_points (nparray): 1D array containing the zero-point
                for each of the bands in this photometric system.
        """
        self.zero_points = zero_points

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
        file_name = replace_file_name(self.config_file, 'filter', 'filter', bp_model, rp_model, self.label)
        file_path = get_file_path(self.config_file)
        self.filter_file = join(file_path, file_name)

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

    def _load_xpsampling_from_xml(self):
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

    def _load_xpmerge_from_xml(self):
        """
        Load the XpMerge table from the filter XML file.
        Returns:
            ndarray: Array containing the sampling grid values.
            dict: A dictionary containing the XpMerge table with one entry for BP and one for RP.
        """
        x_root = get_file_root(self.filter_file)
        sampling_grid, bp_merge, rp_merge = get_xp_merge(x_root)
        return sampling_grid, dict(zip(BANDS, [bp_merge, rp_merge]))
