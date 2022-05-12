"""
xp_sampled_spectrum.py
====================================
Module to represent a BP/RP sampled spectrum.
"""

import numpy as np
from .xp_spectrum import XpSpectrum
from .sampled_spectrum import SampledSpectrum
from .utils import _list_to_array


class XpSampledSpectrum(XpSpectrum, SampledSpectrum):
    """
    A Gaia BP/RP spectrum sampled to a given grid of positions.
    """

    def __init__(
            self,
            source_id=0,
            xp=None,
            pos=None,
            flux=None,
            flux_error=None):

        XpSpectrum.__init__(
            self,
            source_id,
            xp)

        self.pos = pos
        self.n_samples = len(self.pos)
        self.flux = flux
        self.error = flux_error

    @classmethod
    def from_sampled(
            cls,
            source_id,
            xp,
            pos,
            flux,
            flux_error):
        """
        Initialise a spectrum.

        Args:
        source_id (long): The source identifier.
        xp (object): The photometer enum (BP/RP).
        pos (ndarray): The array of positions (in pseudo-wavelength or wavelength) of
            the samples.
        flux (ndarray): The flux value of each sample.
        flux_error (ndarray): The uncertainty on the flux value of each sample.
        """
        return cls(source_id,
                   xp,
                   pos,
                   flux,
                   flux_error)

    @classmethod
    def from_continuous(
            cls,
            continuous_spectrum,
            sampled_basis_functions,
            truncation=-1):
        """
        Initialise a spectrum.

        Args:
            continuous_spectrum (object): The continuous representation of this spectrum.
            sampled_basis_functions (object): The set of basis functions sampled onto
                the grid defining the resolution of the final sampled spectrum.
            truncation (int): Number of bases to be used for this spectrum. The set of
                bases functions used for the continuous representation of the spectra
                has been optimised to ensure that the first bases are the ones that
                contribute most. In many cases, the last bases contribution will be below
                the noise. Truncation of the basis function set to preserve only the
                significant bases is optional. By default, no truncation will be applied,
                i.e. all bases will be used.
        """
        if isinstance(truncation, (int, np.int64)) and truncation > 0:
            coefficients = continuous_spectrum.get_coefficients()[:truncation]
            covariance = continuous_spectrum.get_covariance()[
                :truncation, :truncation]
            design_matrix = sampled_basis_functions._get_design_matrix()[
                :truncation][:]
        else:
            coefficients = continuous_spectrum.get_coefficients()
            covariance = continuous_spectrum.get_covariance()
            design_matrix = sampled_basis_functions._get_design_matrix()

        pos = sampled_basis_functions._get_sampling_grid()
        flux = SampledSpectrum._sample_flux(coefficients, design_matrix)
        flux_error = SampledSpectrum._sample_error(
            covariance,
            design_matrix,
            continuous_spectrum.get_standard_deviation())

        return cls(continuous_spectrum.get_source_id(),
                   continuous_spectrum.get_xp(),
                   pos,
                   flux,
                   flux_error)

    def _spectrum_to_dict(self):
        """
        Represent spectrum as dictionary.

        Returns:
            dict: A dictionary populated with the minimum set of parameters that
                need to be stored for this object. This is optimised for writing
                large number of sampled spectra and for this reason the array of
                positions is NOT included as it is expected to be the same for
                a batch of spectra. The array fo positions can be retrieved calling
                the sampling_to_dict method.
        """
        return {
            'source_id': self.source_id,
            'xp': self.xp.upper(),
            'flux': _list_to_array(self.flux),
            'flux_error': _list_to_array(self.error)
        }

    def _sampling_to_dict(self):
        """
        Represent sampling as dictionary.

        Returns:
            dict: A dictionary populated with the sampling grid used for this spectrum.
        """
        return {
            'pos': _list_to_array(self.pos)
        }

    def _get_fluxes(self):
        return self.flux

    def _get_flux_errors(self):
        return self.error

    def _get_positions(self):
        return self.pos

    @classmethod
    def _get_flux_label(cls):
        return "Flux [e-/s]"

    @classmethod
    def _get_position_label(cls):
        return "Pseudo-wavelength"
