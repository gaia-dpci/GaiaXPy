"""Representation of BP/RP spectra."""

from .generic_spectrum import Spectrum
from ..core.generic_functions import parse_band


class XpSpectrum(Spectrum):
    """Associate a source ID with the BP or RP photometer."""

    def __init__(self, source_id, band):
        """Store the source ID and normalise the photometer name.

        Args:
            source_id (int or str): Source identifier.
            band (str): BP or RP, ignoring case. A one-item list of the name
                is also accepted.

        Raises:
            InvalidBandError: The supplied name is not a recognised photometer.
        """
        Spectrum.__init__(self, source_id)
        self.band = parse_band(band)

    def get_band(self):
        """Return the photometer name.

        Returns:
            str: Lowercase 'bp' or 'rp'.
        """
        return self.band
