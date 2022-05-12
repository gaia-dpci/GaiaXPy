"""
xp_spectrum.py
====================================
Module to represent a BP/RP spectrum.
"""

from .generic_spectrum import Spectrum


class XpSpectrum(Spectrum):
    """
    A spectrum observed with one of the Gaia low-resolution photometers
    (Blue or Red Photometer, BP or RP).
    """
    def __init__(
            self,
            source_id,
            xp):
        """
        Initialise an XP spectrum.

        Args:
            source_id (str): Source identifier.
            xp (str): Gaia photometer, can be either 'bp' or 'rp'.
        """
        Spectrum.__init__(self, source_id)
        self.xp = xp

    def get_xp(self):
        """
        Get band.

        Returns:
            str: Photometer identifier. Either 'bp' or 'rp'.
        """
        return self.xp
