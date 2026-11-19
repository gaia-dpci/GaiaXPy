"""Evaluate fluxes, flux errors and magnitudes in one photometric system.

Importing this module installs a filter suppressing RuntimeWarning messages.
The magnitude calculation also handles non-positive flux explicitly.
"""

import warnings

import numpy as np

from .photometric_absolute_sampled_spectrum import PhotometricAbsoluteSampledSpectrum

# Ignore negative flux, handled in the code.
warnings.filterwarnings('ignore', category=RuntimeWarning)


class SingleSyntheticPhotometry(PhotometricAbsoluteSampledSpectrum):
    """Synthetic photometry for one source and one selected system.

    The supplied design matrices already describe passband integration. After
    combining BP and RP, the selected system applies its flux and error
    corrections, then converts corrected fluxes to magnitudes.
    """

    def __init__(self, source_id, xp_spectra, sampled_bases, merge, truncation, photometric_system):
        """Evaluate passband fluxes, apply system corrections and calculate magnitudes.

        Args:
            source_id (int or str): Source identifier.
            xp_spectra (dict): Continuous BP/RP spectra keyed by photometer.
            sampled_bases (dict): Per-band passband-integral design matrices wrapped
                in SampledBasisFunctions, with one column per passband.
            merge (dict): Per-band weights in the same passband order.
            truncation (dict or None): Recommended number of basis functions for
                each photometer, keyed by 'bp' and 'rp'. When truncation is enabled,
                the calling operation passes this source's bp_n_relevant_bases
                and rp_n_relevant_bases values. None or an empty dictionary uses
                all available basis functions, as does a missing or non-positive
                count for an individual photometer.
            photometric_system (PhotometricSystem): Selected member, including its
                version for an additional system. Its value supplies corrections
                and zero points.

        Notes:
            Error correction receives the original, uncorrected flux. Magnitudes
            use corrected flux. Both photometers are required; with only one,
            passband fluxes, flux errors and magnitudes are NaN.
        """
        PhotometricAbsoluteSampledSpectrum.__init__(self, source_id, xp_spectra, sampled_bases, merge,
                                                    truncation=truncation)
        self.photometric_system = photometric_system.value
        # Correct flux if necessary (regular Photometric systems return the original value)
        aux_flux = self.flux
        self.flux = self.photometric_system.standardised_system_flux_correction(aux_flux)
        # Correct the errors
        self.flux_error = self.photometric_system.standardised_system_error_correction(aux_flux, self.flux_error)
        # Magnitude is computed from self.flux which is the corrected flux
        self.mag = self._compute_mag()

    def _compute_mag(self) -> list:
        """Convert corrected passband fluxes to magnitudes using system zero points.

        Returns:
            list[float]: -2.5 * log10(flux) + zero_point in passband order. Fluxes
            that are zero or negative give NaN magnitudes; missing flux remains NaN.
        """
        flux = np.asarray(self.flux)
        zero_points = np.asarray(self.photometric_system.get_zero_points())

        with np.errstate(divide='ignore', invalid='ignore'):
            magnitudes = -2.5 * np.log10(flux) + zero_points

        magnitudes[flux <= 0] = np.nan
        return magnitudes.tolist()
