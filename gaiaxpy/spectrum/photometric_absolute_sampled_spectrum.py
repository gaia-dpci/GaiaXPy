import numpy as np

from gaiaxpy.core.custom_errors import InvalidBandError
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum


class PhotometricAbsoluteSampledSpectrum(AbsoluteSampledSpectrum):

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
            if existing_band not in BANDS:
                raise InvalidBandError(existing_band)
            self.flux = np.full_like(spectrum['flux'], np.nan)
            self.error = np.full_like(spectrum['error'], np.nan)
            if with_correlation:
                self.covariance = np.full_like(spectrum['cov'], np.nan)
