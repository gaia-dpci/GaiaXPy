"""
standardised_photometric_system.py
====================================
Module to represent a standardised photometric system.
"""

from gaiaxpy.core.generic_functions import _get_system_label
from .internal_photometric_system import InternalPhotometricSystem


class StandardisedPhotometricSystem(InternalPhotometricSystem):

    def __init__(self, name):
        """
        A photometric system is defined by the set of bands available.

        Args:
            name (str): Name of the PhotometricSystem
        """
        super().__init__(name)
        self._load_offset_from_xml()

    def _correct_flux(self, flux):
        flux_corr = flux + self.offsets
        return flux_corr

    def _correct_error(self, flux, error):
        eef = (flux + self.offsets) / flux
        eef = abs(eef)
        flux_error_corr = error * eef
        return flux_error_corr
