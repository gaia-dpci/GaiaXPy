"""
absolute_sampled_spectrum.py
====================================
Module to represent an absolute sampled spectrum.
"""

from numbers import Number

import numpy as np

from .sampled_spectrum import SampledSpectrum
from .utils import _list_to_array
from ..core.custom_errors import NoBandsAvailableError
from ..core.generic_functions import correlation_from_covariance


class AbsoluteSampledSpectrum(SampledSpectrum):
    """
    A spectrum calibrated onto the absolute system of wavelength and flux. The spectrum is represented by a set of
    discrete measurements or samples.
    """

    def __init__(self, source_id, xp_spectra, sampled_bases, merge, truncation=None, with_correlation=False):
        """
        Initialise an absolute sampled spectrum.

        Args:
            source_id (str): Source identifier.
            xp_spectra (dict): A dictionary containing the BP and RP continuous spectra.
            sampled_bases (dict): The set of basis functions sampled onto the grid defining the resolution of the final
                sampled spectrum.
            merge (dict): The weighting factors for BP and RP sampled onto the grid defining the resolution of the final
                sampled spectrum.
            truncation (dict): Number of bases to be used for this spectrum. The set of bases functions used for the
                continuous representation of the spectra has been optimised to ensure that the first bases are the ones
                that contribute most. In many cases, the last bases contribution will be below the noise. Truncation of
                the basis function set to preserve only the significant bases is optional. By default, no truncation
                will be applied, i.e. all bases will be used.
            with_correlation (bool): Whether correlation information should be computed.
        """
        self.truncation = dict() if truncation is None else truncation
        self.available_bands = self.get_available_bands(xp_spectra)
        if not self.available_bands:
            raise NoBandsAvailableError()
        pos = sampled_bases[self.available_bands[0]].get_sampling_grid()
        SampledSpectrum.__init__(self, source_id, pos)
        self.pos = pos

    @staticmethod
    def get_available_bands(xp_spectra):
        def __is_available_band(_xp_spectra, band):
            return isinstance(_xp_spectra[band].covariance, np.ndarray)

        return [band for band in xp_spectra.keys() if __is_available_band(xp_spectra, band)]

    def generate_spectra(self, xp_spectra, sampled_bases, with_correlation):
        split_spectrum = {band: dict() for band in self.available_bands}
        for band in self.available_bands:
            band_truncation = self.truncation.get(band)
            split_spectrum[band]['xp_spectra'] = xp_spectra[band]
            stdev = split_spectrum[band]['xp_spectra'].get_standard_deviation()
            design_matrix = sampled_bases[band].get_design_matrix()
            spectra_covariance = split_spectrum[band]['xp_spectra'].get_covariance()
            coefficients = split_spectrum[band]['xp_spectra'].get_coefficients()
            if isinstance(band_truncation, Number) and band_truncation > 0:
                design_matrix = design_matrix[:band_truncation][:]
                spectra_covariance = spectra_covariance[:band_truncation, :band_truncation]
                coefficients = coefficients[:band_truncation]
            split_spectrum[band]['flux'] = self._sample_flux(coefficients, design_matrix)
            split_spectrum[band]['error'] = self._sample_error(spectra_covariance, design_matrix, stdev)
            if with_correlation:
                split_spectrum[band]['cov'] = self._sample_covariance(spectra_covariance, design_matrix)
                split_spectrum[band]['stdev'] = stdev
        return split_spectrum

    def __merge_output(self, split_spectrum, merge, with_correlation):
        raise NotImplementedError('Method not implemented for base class.')

    def _get_fluxes(self):
        return self.flux

    def _get_flux_errors(self):
        return self.error

    def get_positions(self):
        return self.pos

    @classmethod
    def get_units(cls):
        return {'flux': 'W.nm**-1.m**-2', 'flux_error': 'W.nm**-1.m**-2', 'pos': 'nm'}

    @classmethod
    def get_flux_label(cls):
        return r'Flux [$\mathrm{W\,nm^{-1}\,m^{-2}}$]'

    @classmethod
    def get_position_label(cls):
        return r'Wavelength [$\mathrm{nm}$]'

    def spectrum_to_dict(self, with_correlation):
        """
        Represent the spectrum as a dictionary.

        Returns:
            dict: A dictionary populated with the minimum set of parameters that need to be stored for this object.
                This is optimised for writing large number of sampled spectra and for this reason the array of positions
                is NOT included as it is expected to be the same for a batch of spectra. The array of positions can be
                retrieved calling the sampling_to_dict method.
        """
        spectrum_dict = {'source_id': self.source_id, 'flux': _list_to_array(self.flux),
                         'flux_error': _list_to_array(self.error)}
        if with_correlation:
            full_correlation = correlation_from_covariance(self.covariance)
            spectrum_dict['correlation'] = full_correlation[np.tril_indices(full_correlation.shape[0], k=-1)]
        return spectrum_dict

    def _sampling_to_dict(self):
        """
        Represent the sampling grid as a dictionary.

        Returns:
            dict: A dictionary populated with the sampling grid used for this spectrum.
        """
        return {'pos': _list_to_array(self.pos)}
