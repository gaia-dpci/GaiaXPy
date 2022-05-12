"""
regular_photometric_system.py
====================================
Module to represent a regular photometric system.
"""

from .internal_photometric_system import InternalPhotometricSystem


class RegularPhotometricSystem(InternalPhotometricSystem):

    def __init__(self, name):
        """
        A photometric system is defined by the set of bands available.

        Args:
            name (str): Name of the PhotometricSystem
        """
        super().__init__(name)

    def _correct_flux(self, flux):
        return flux

    def _correct_error(self, flux, error):
        return error
