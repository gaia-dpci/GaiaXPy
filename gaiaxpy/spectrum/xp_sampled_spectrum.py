"""
xp_sampled_spectrum.py
====================================
Module to represent a BP/RP sampled spectrum.
"""

from numbers import Number

import numpy as np

from .sampled_spectrum import SampledSpectrum
from .utils import _list_to_array
from .xp_spectrum import XpSpectrum
from ..core.generic_functions import correlation_from_covariance


class XpSampledSpectrum(XpSpectrum, SampledSpectrum):
    """
    A Gaia BP/RP spectrum sampled to a given grid of positions.
    """

    def __init__(self, source_id=0, xp=None, pos=None, flux=None, flux_error=None, cov=None, stdev=None):
        XpSpectrum.__init__(self, source_id, xp)
        self.pos = pos
        self.n_samples = len(self.pos)
        self.flux = flux
        self.error = flux_error
        self.stdev = stdev
        self.covariance = cov

    @classmethod
    def from_data_frame(cls, df, sampling, band):
        """
        Initialise a sampled spectrum from a Pandas DataFrame.

        Args:
            df (DataFrame): DataFrame containing at least the fields source_id, flux, flux_error, cov The same
                structure as used in the archive for the correlation matrix is expected.
            sampling (ndarray): Given sampling.
            band (str): Gaia photometer, can be either 'bp' or 'rp'.
        """
        return cls(df['source_id'], band, sampling, df['flux'], df['flux_error'], df['cov'])

    @classmethod
    def from_sampled(cls, source_id, xp, pos, flux, flux_error, cov=None):
        """
        Initialise a spectrum.

        Args:
        source_id (long): The source identifier.
        xp (object): The photometer enum (BP/RP).
        pos (ndarray): The array of positions (in pseudo-wavelength or wavelength) of the samples.
        flux (ndarray): The flux value of each sample.
        flux_error (ndarray): The uncertainty on the flux value of each sample.
        cov (ndarray): The covariance matrix.
        """
        return cls(source_id, xp, pos, flux, flux_error, cov)

    @classmethod
    def from_continuous(cls, continuous_spectrum, sampled_basis_functions, truncation=-1, with_correlation=False):
        """
        Initialise a spectrum.

        Args:
            continuous_spectrum (XpContinuousSpectrum): The continuous representation of this spectrum.
            sampled_basis_functions (SampledBasisFunctions): The set of basis functions sampled onto the grid defining
                the resolution of the final sampled spectrum.
            truncation (int): Number of bases to be used for this spectrum. The set of bases functions used for the
                continuous representation of the spectra has been optimised to ensure that the first bases are the ones
                that contribute most. In many cases, the last bases contribution will be below the noise. Truncation of
                the basis function set to preserve only the significant bases is optional. By default, no truncation
                will be applied, i.e. all bases will be used.
            with_correlation (bool): Whether correlation information should be generated.
        """
        if continuous_spectrum and sampled_basis_functions:
            coefficients = continuous_spectrum.get_coefficients()
            design_matrix = sampled_basis_functions.get_design_matrix()
        else:
            return None
        covariance = continuous_spectrum.get_covariance()

        if isinstance(truncation, Number) and truncation > 0:
            coefficients = coefficients[:truncation]
            covariance = covariance[:truncation, :truncation]
            design_matrix = design_matrix[:truncation][:]

        stdev = continuous_spectrum.get_standard_deviation()
        pos = sampled_basis_functions.get_sampling_grid()
        flux = SampledSpectrum._sample_flux(coefficients, design_matrix)
        flux_error = SampledSpectrum._sample_error(covariance, design_matrix, stdev)
        cov = SampledSpectrum._sample_covariance(covariance, design_matrix) if with_correlation else None
        return cls(continuous_spectrum.get_source_id(), continuous_spectrum.get_xp(), pos, flux, flux_error, cov, stdev)

    def spectrum_to_dict(self):
        """
        Represent spectrum as dictionary.

        Returns:
            dict: A dictionary populated with the minimum set of parameters that need to be stored for this object. This
                is optimised for writing large number of sampled spectra and for this reason the array of positions is
                NOT included as it is expected to be the same for a batch of spectra. The array of positions can be
                retrieved by calling the sampling_to_dict method.
        """
        spectrum_dict = {'source_id': self.source_id, 'xp': self.xp.upper(), 'flux': _list_to_array(self.flux),
                         'flux_error': _list_to_array(self.error)}
        if self.covariance is not None:
            full_correlation = correlation_from_covariance(self.covariance)
            spectrum_dict['correlation'] = full_correlation[np.tril_indices(full_correlation.shape[0], k=-1)]
            if self.stdev is not None:
                spectrum_dict['standard_deviation'] = self.stdev
        return spectrum_dict

    def _sampling_to_dict(self):
        """
        Represent sampling as dictionary.

        Returns:
            dict: A dictionary populated with the sampling grid used for this spectrum.
        """
        return {'pos': _list_to_array(self.pos)}

    def _get_fluxes(self):
        return self.flux

    def _get_flux_errors(self):
        return self.error

    def get_positions(self):
        return self.pos

    def _get_covariance(self):
        return self.covariance

    @classmethod
    def get_units(cls):
        return {'flux': 'electron/s', 'flux_error': 'electron/s', 'standard_deviation': 'electron/s', 'pos': 'pwl'}

    @classmethod
    def get_flux_label(cls):
        return "Flux [e-/s]"

    @classmethod
    def get_position_label(cls):
        return "Pseudo-wavelength"
