"""
single_synthetic_photometry.py
====================================
Module to represent a synthetic photometry in a single photometric system.
"""

import warnings

import numpy as np

from .photometric_absolute_sampled_spectrum import PhotometricAbsoluteSampledSpectrum

# Ignore negative flux, handled in the code.
warnings.filterwarnings('ignore', category=RuntimeWarning)


class SingleSyntheticPhotometry(PhotometricAbsoluteSampledSpectrum):
    """
    Synthetic photometry derived from Gaia spectra in one photometric system.
    """

    def __init__(self, source_id, xp_spectra, sampled_bases, merge, truncation, photometric_system):
        """
        Initialise a synthetic photometry in a single photometric system.

        Args:
            source_id (str): Source identifier.
            xp_spectra (dict): A dictionary containing the BP and RP continuous spectra.
            sampled_bases (dict): The set of basis functions sampled onto the grid defining the resolution of the final
                sampled spectrum.
            merge (dict): The weighting factors for BP and RP sampled onto the grid defining the resolution of the final
                sampled spectrum.
            truncation (dict): The number of relevant bases per band.
            photometric_system (PhotometricSystem): The photometric system of the synthetic photometry.
        """
        PhotometricAbsoluteSampledSpectrum.__init__(self, source_id, xp_spectra, sampled_bases, merge,
                                                    truncation=truncation)
        self.photometric_system = photometric_system.value
        # Correct flux if necessary (regular Photometric systems return the original value)
        aux_flux = self.flux
        self.flux = self.photometric_system._correct_flux(aux_flux)
        # Correct the errors
        self.error = self.photometric_system._correct_error(aux_flux, self.error)
        # Magnitude is computed from self.flux which is the corrected flux
        self.mag = self._compute_mag()

    def _photometry_to_dict(self):
        """
        Represent the photometry as a dictionary.

        Returns:
            dict: A dictionary containing the source identifier and the synthetic photometry.
        """
        phot = {'source_id': self.source_id}
        mag = self._field_to_dict(self.mag, 'mag')
        flux = self._field_to_dict(self.flux, 'flux')
        error = self._field_to_dict(self.error, 'flux_error')
        return {**phot, **mag, **flux, **error}

    def _field_to_dict(self, field, name):
        """
        Represent the field as a dictionary.

        Returns:
            dict: A dictionary containing a particular field of the synthetic photometry.
        """
        bands = self.photometric_system.get_bands()
        values = field
        return {f'{name}_{band}': values[i] for i, band in enumerate(bands)}

    def _compute_mag(self):
        def flux_to_mag(flux, zero_point):
            """
            Convert flux to magnitude.

            Args:
                flux (float): Flux value.
                zero_point (float): Photometric zero-point.

            Returns:
                float: The magnitude.
            """
            if flux <= 0:
                return np.nan
            result = -2.5 * np.log10(flux) + zero_point
            return result

        return [flux_to_mag(flux, zero_point) for flux, zero_point in
                zip(self.flux, self.photometric_system.get_zero_points())]
