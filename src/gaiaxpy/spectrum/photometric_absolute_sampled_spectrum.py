"""Merge BP/RP passband contributions for synthetic photometry."""
import numpy as np

from gaiaxpy.core.custom_errors import InvalidBandError
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum


class PhotometricAbsoluteSampledSpectrum(AbsoluteSampledSpectrum):
    """Fluxes evaluated through passbands.

    The design matrices represent passband integrals rather than wavelength
    samples. If only one photometer is available, all output fluxes and
    uncertainties are NaN, including covariance when requested.
    """

    def __init__(self, source_id, xp_spectra, sampled_bases, merge, truncation=None, with_correlation=False):
        """Evaluate and merge the BP/RP contributions for each passband.

        Args:
            source_id (int or str): Source identifier.
            xp_spectra (dict): Continuous spectra keyed by 'bp' and/or 'rp'.
            sampled_bases (dict): SampledBasisFunctions objects keyed by photometer,
                using the same passband order and one matrix column per passband.
            merge (dict): BP and RP weights on that output grid.
            truncation (dict or None): Recommended number of basis functions for
                each photometer, keyed by 'bp' and 'rp'. When truncation is enabled,
                the calling operation passes this source's bp_n_relevant_bases
                and rp_n_relevant_bases values. None or an empty dictionary uses
                all available basis functions.
            with_correlation (bool): Retain projected covariance for correlations.

        Raises:
            NoBandsAvailableError: Neither supplied spectrum has a NumPy covariance
                array.
        """
        super().__init__(source_id, xp_spectra, sampled_bases, merge, truncation=truncation,
                         with_correlation=with_correlation)
        split_spectrum = self.generate_spectra(xp_spectra, sampled_bases, with_correlation=with_correlation)
        self.__merge_output(split_spectrum)

    def __merge_output(self, split_spectrum):
        """Merge two-band passband results or fill a single-band result with NaNs.

        Args:
            split_spectrum (dict): Per-band fluxes and uncertainties, plus optional
                covariance.

        Raises:
            InvalidBandError: A single available band is neither 'bp' nor 'rp'.
        """
        n_bands = len(split_spectrum.keys())
        # If both bands are present
        if n_bands == 2:
            self.merge_variables(split_spectrum)
        # If only one is
        elif n_bands == 1:
            existing_band, spectrum = list(split_spectrum.items())[0]
            if existing_band not in BANDS:
                raise InvalidBandError(existing_band)
            self.flux = np.full_like(spectrum['flux'], np.nan)
            self.flux_error = np.full_like(spectrum['flux_error'], np.nan)
            if self.with_correlation:
                self.covariance = np.full_like(spectrum['cov'], np.nan)
