import numpy as np

from gaiaxpy.core.satellite import BANDS, RP_WL, BP_WL
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum


class CalibrationAbsoluteSampledSpectrum(AbsoluteSampledSpectrum):

    def __init__(self, source_id, xp_spectra, sampled_bases, merge, truncation=None, with_correlation=False):
        super().__init__(source_id, xp_spectra, sampled_bases, merge, truncation=truncation,
                         with_correlation=with_correlation)
        split_spectrum = self.generate_spectra(xp_spectra, sampled_bases, with_correlation=with_correlation)
        self.__merge_output(split_spectrum, merge, with_correlation=with_correlation)

    def __merge_output(self, split_spectrum, merge, with_correlation):
        n_bands = len(split_spectrum.keys())
        # If both bands are present
        if n_bands == 2:
            self.flux = np.add(np.multiply(split_spectrum[BANDS.bp]['flux'], merge[BANDS.bp]),
                               np.multiply(split_spectrum[BANDS.rp]['flux'], merge[BANDS.rp]))
            self.error = np.sqrt(np.add(np.multiply(split_spectrum[BANDS.bp]['error'] ** 2, merge[BANDS.bp] ** 2),
                                        np.multiply(split_spectrum[BANDS.rp]['error'] ** 2, merge[BANDS.rp] ** 2)))
            if with_correlation:
                self.covariance = np.add(np.multiply(split_spectrum[BANDS.bp]['cov'], merge[BANDS.bp]),
                                         np.multiply(split_spectrum[BANDS.rp]['cov'], merge[BANDS.rp]))
        # If only one is
        elif n_bands == 1:
            existing_band, spectrum = list(split_spectrum.items())[0]
            self.flux = spectrum['flux']
            self.error = spectrum['error']
            if with_correlation:
                self.covariance = spectrum['cov']
            # Patch values if a band is missing
            masked_pos = self.pos.copy()
            masked_pos = masked_pos.astype(float)
            if existing_band == BANDS.rp:
                masked_pos[masked_pos <= RP_WL.low] = np.nan
            elif existing_band == BANDS.bp:
                masked_pos[masked_pos >= BP_WL.high] = np.nan
            else:
                raise ValueError(f'Band {existing_band} is not a valid band.')
            # Get the indices of all the values in pos that are smaller than the lowest RP range value
            self.flux[np.argwhere(np.isnan(masked_pos))] = np.nan
            self.error[np.argwhere(np.isnan(masked_pos))] = np.nan
            if with_correlation:
                self.covariance[:, np.argwhere(np.isnan(masked_pos))] = np.nan
                self.covariance[np.argwhere(np.isnan(masked_pos)), :] = np.nan
