"""
generic_spectrum.py
====================================
Module to represent a generic spectrum.
"""


class Spectrum(object):
    """
    Base spectrum. Contain only the source ID.
    """

    def __init__(
            self,
            source_id):
        """
        Initialise a spectrum.

        Args:
            source_id (str): Source identifier. Can be a Gaia source ID (long) or any
                other source identifier.
        """
        self.source_id = source_id

    def get_source_id(self):
        """
        Get the source ID of the spectrum.

        Returns:
            str: Source identifier.
        """
        return self.source_id
