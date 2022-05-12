"""
standardised_photometric_system.py
====================================
Module to represent a standardised photometric system.
"""

from .internal_photometric_system import InternalPhotometricSystem
from gaiaxpy.core import _load_offset_from_csv


class StandardisedPhotometricSystem(InternalPhotometricSystem):

    def __init__(self, name):
        """
        A photometric system is defined by the set of bands available.

        Args:
            name (str): Name of the PhotometricSystem
        """
        super().__init__(name)
        offsets = _load_offset_from_csv(name)
        self.set_offsets(offsets)

    def _correct_flux(self, flux):
        flux_corr = flux + self.offsets
        return flux_corr

    def _correct_error(self, flux, error):
        eef = (flux + self.offsets) / flux
        eef = abs(eef)
        flux_error_corr = error * eef
        return flux_error_corr
