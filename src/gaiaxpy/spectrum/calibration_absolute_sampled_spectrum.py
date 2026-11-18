"""Merge calibrated BP/RP samples and handle a missing photometer."""
import numpy as np

from gaiaxpy.core.dispersion_function import wl_range
from gaiaxpy.core.generic_functions import lower_correlation_from_covariance
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum


class CalibrationAbsoluteSampledSpectrum(AbsoluteSampledSpectrum):
    """Calibrated samples with BP/RP merging or single-band wavelength masking.

    With both photometers available, contributions use the supplied merge weights.
    With one available, samples beyond that band's configured wavelength limit
    are set to NaN, including associated error and covariance entries.
    """

    def __init__(self, source_id, xp_spectra, sampled_bases, merge, release, *,
                 truncation=None, with_correlation=False):
        """Evaluate the available spectra and prepare calibrated output samples.

        Args:
            source_id (int or str): Source identifier.
            xp_spectra (dict): Continuous spectra keyed by 'bp' and/or 'rp'.
            sampled_bases (dict): SampledBasisFunctions objects keyed by photometer,
                using the same output grid and basis-by-sample matrix layout.
            merge (dict): BP and RP weights on that output grid.
            release (str): Gaia release used to select the single-band wavelength limits.
            truncation (dict or None): Recommended number of basis functions for
                each photometer, keyed by 'bp' and 'rp'. When truncation is enabled,
                the calling operation passes this source's bp_n_relevant_bases
                and rp_n_relevant_bases values. None or an empty dictionary uses
                all available basis functions, as does a missing or non-positive
                count for an individual photometer.
            with_correlation (bool): Retain projected covariance for correlations.

        Raises:
            NoBandsAvailableError: Neither supplied spectrum has a NumPy covariance
                array.
        """
        super().__init__(source_id, xp_spectra, sampled_bases, merge, truncation=truncation,
                         with_correlation=with_correlation)
        split_spectrum = self.generate_spectra(xp_spectra, sampled_bases, with_correlation=with_correlation)
        self.__merge_output(split_spectrum, release)

    def __merge_output(self, split_spectrum, release):
        """Merge both bands or mask the unsupported end of a single-band result.

        Args:
            split_spectrum (dict): Available band results from generate_spectra.
            release (str): Release selecting the configured wavelength limits.

        Notes:
            RP-only values at or below the lower RP limit are masked. BP-only values
            at or above the upper BP limit are masked. Sample positions are retained.
            With covariance enabled, corresponding rows and columns are also masked.
        """
        n_bands = len(split_spectrum.keys())
        # If both bands are present
        if n_bands == 2:
            self.merge_variables(split_spectrum)
        # If only one is
        elif n_bands == 1:
            existing_band, spectrum = list(split_spectrum.items())[0]
            self.flux = spectrum['flux']
            self.flux_error = spectrum['flux_error']
            if self.with_correlation:
                self.covariance = spectrum['cov']
            # Patch values if a band is missing
            masked_pos = self.pos.copy()
            masked_pos = masked_pos.astype(float)
            rp_low = wl_range(BANDS.rp, release).low
            bp_high = wl_range(BANDS.bp, release).high
            if existing_band == BANDS.rp:
                masked_pos[masked_pos <= rp_low] = np.nan
            elif existing_band == BANDS.bp:
                masked_pos[masked_pos >= bp_high] = np.nan
            else:
                raise ValueError(f'Band {existing_band} is not a valid band.')
            # Get the indices of all the values in pos that are smaller than the lowest RP range value
            self.flux[np.argwhere(np.isnan(masked_pos))] = np.nan
            self.flux_error[np.argwhere(np.isnan(masked_pos))] = np.nan
            if self.with_correlation:
                self.covariance[:, np.argwhere(np.isnan(masked_pos))] = np.nan
                self.covariance[np.argwhere(np.isnan(masked_pos)), :] = np.nan

    def spectrum_to_tuple(self, with_correlation):
        """Arrange calibrated values for output.

        Args:
            with_correlation (bool): Append packed sample correlations, calculated
                from the stored covariance. Requires covariance to be populated.

        Returns:
            tuple: source_id, flux and flux_error, optionally followed by lower-triangle
            correlations without the diagonal. Wavelengths are returned separately
            by the calling operation.
        """
        if with_correlation:
            correlation = lower_correlation_from_covariance(self.covariance)
            return self.source_id, self.flux, self.flux_error, correlation

        return self.source_id, self.flux, self.flux_error
