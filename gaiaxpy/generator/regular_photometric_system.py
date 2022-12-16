"""
regular_photometric_system.py
====================================
Module to represent a regular photometric system.
"""
from os.path import join

from .internal_photometric_system import InternalPhotometricSystem
from ..config.paths import config_path


class RegularPhotometricSystem(InternalPhotometricSystem):

    def __init__(self, name, config_file=None):
        """
        A photometric system is defined by the set of bands available.

        Args:
            name (str): Name of the PhotometricSystem
        """
        config_file = join(config_path, 'config.ini') if not config_file else config_file
        super().__init__(name, config_file)

    def _correct_flux(self, flux):
        return flux

    def _correct_error(self, flux, error):
        return error
