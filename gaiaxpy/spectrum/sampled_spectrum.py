"""
sampled_spectrum.py
====================================
Module to represent a sampled spectrum.
"""

import numpy as np
from numpy import ndarray, nan

from .generic_spectrum import Spectrum


class SampledSpectrum(Spectrum):
    """
    A spectrum defined by a set of discrete measurements. Each measurement is defined by a position in wavelength (or
    pseudo-wavelength), a measured flux and an associated flux error.
    Specific implementations of this class will define the units in use for positions and fluxes.
    """

    def __init__(self, source_id, sampling_grid):
        """
        Initialise a sampled spectrum.

        Args:
            source_id (str): Source identifier.
            sampling_grid (ndarray): 1D array containing the positions of the samples (or discrete measurements) for
                this spectrum.
        """
        Spectrum.__init__(self, source_id)
        self.n_samples = np.size(sampling_grid)

        self.pos = None
        self.flux = None
        self.error = None
        self.covariance = None

    def _get_fluxes(self):
        """
        Get the flux samples.

        Returns:
            ndarray: 1D array containing all flux samples.
        """
        return self.flux

    def _get_flux_errors(self):
        """
        Get the flux errors of each sample.

        Returns:
            ndarray: 1D array containing the error in flux for all samples.
        """
        return self.error

    def _get_covariance(self):
        """
        Get the flux covariance matrix.

        Returns:
            ndarray: 2D array containing the flux covariance matrix.
        """
        return self.covariance

    def get_positions(self):
        """
        Get the positions of all samples.

        Returns:
            ndarray: 1D array containing the position of all samples.
        """
        return self.pos

    def get_flux_label(self):
        """
        Get the labels describing the flux measurements.

        Returns:
            str: Short description of the flux measurements, including the units.
        """
        return ""

    def get_position_label(self):
        """
        Get the positions of the samples, including the units.

        Returns:
            str: Short description of the positions of the samples.
        """
        return ""

    def _get_inputs(self, spectrum):
        return spectrum.get_positions(), spectrum._get_fluxes(), spectrum._get_flux_errors()

    @staticmethod
    def _sample_flux(coefficients, design_matrix):
        """
        Given a set of coefficients to be applied to a set of basis functions and a design matrix containing the
        evaluation of each basis function at the positions corresponding to the samples, this method computes the flux
        values for each sample.

        Args:
            coefficients (ndarray): 1D array containing the coefficients multiplying the basis functions in the
                continuous representation.
            design_matrix (ndarray): 2D array containing the evaluation of the basis functions on the desired sampling
                grid.

        Returns:
            ndarray: 1D array containing the flux values for all samples.
        """
        if isinstance(coefficients, ndarray) and coefficients.size > 0:
            return coefficients @ design_matrix
        return nan

    @staticmethod
    def _sample_error(covariance, design_matrix, standard_deviation):
        """
        Given the covariance matrix and standard deviation of the least squares solution defining the continuous
        representation of the spectrum in terms of basis functions and a design matrix containing the evaluation of each
        basis function at the positions corresponding to the samples, this method computes the error associated to the
        flux value for each sample.

        Args:
            covariance (ndarray): 2D array containing the elements of the covariance matrix.
            design_matrix (ndarray): 2D array containing the evaluation of the basis functions on the desired sampling
                grid.
            standard_deviation (float): Standard deviation.

        Returns:
            ndarray: 1D array containing the errors in flux for all samples.
        """
        if len(covariance) == 0:
            return covariance
        return np.sqrt(np.sum(np.multiply(design_matrix.T @ covariance, design_matrix.T), axis=1)) * standard_deviation

    @staticmethod
    def _sample_covariance(covariance, design_matrix):
        """
        Given the covariance matrix and a design matrix containing the evaluation of each basis function at the
        positions corresponding to the samples, this method computes the covariance matrix of the sampled spectrum.

        Args:
            covariance (ndarray): 2D array containing the elements of the covariance matrix of the continuous
                representation.
            design_matrix (ndarray): 2D array containing the evaluation of the basis functions on the desired sampling
            grid.

        Returns:
            ndarray: 2D array containing the covariance matrix of the sampled spectrum.
        """
        return design_matrix.T @ covariance @ design_matrix
