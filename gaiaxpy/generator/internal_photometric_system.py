"""
internal_photometric_system.py
====================================
Module for the parent class of the standardised and regular photometric systems.
"""

from gaiaxpy.core import _load_xpzeropoint_from_csv


class InternalPhotometricSystem(object):

    def __init__(self, name):
        self.label = name
        bands, zero_points = _load_xpzeropoint_from_csv(name)
        self.set_bands(bands)
        self.set_zero_points(zero_points)

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
