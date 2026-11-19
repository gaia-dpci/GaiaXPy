"""Shared storage and coefficient projection for sampled spectra."""

import numpy as np
from numpy import ndarray, nan

from .generic_spectrum import Spectrum


class SampledSpectrum(Spectrum):
    """Base class for flux samples, flux errors and optional covariance.

    Subclasses supply the sample positions, flux values and units. Design matrices
    in this package have one row per basis function and one column per sample.
    """

    def __init__(self, source_id, sampling_grid):
        """Store the source ID and number of samples, leaving sample data unset.

        Args:
            source_id (int or str): Source identifier.
            sampling_grid (array-like): Grid used to determine n_samples. The base
                constructor does not retain this grid as pos.

        Notes:
            pos, flux, flux_error and covariance are initially None.
        """
        Spectrum.__init__(self, source_id)
        self.n_samples = np.size(sampling_grid)

        self.pos = None
        self.flux = None
        self.flux_error = None
        self.covariance = None

    def _get_fluxes(self):
        """Return the stored flux samples without copying.

        Returns:
            numpy.ndarray or None: Stored one-dimensional array, or None if unset.
        """
        return self.flux

    def _get_flux_errors(self):
        """Return the stored flux errors without copying.

        Returns:
            numpy.ndarray or None: Stored one-dimensional array, or None if unset.
        """
        return self.flux_error

    def _get_covariance(self):
        """Return the stored sample covariance without copying.

        Returns:
            numpy.ndarray or None: Stored two-dimensional array, or None if unset.
        """
        return self.covariance

    def get_positions(self):
        """Return the stored sample positions without copying.

        Returns:
            numpy.ndarray or None: Stored one-dimensional array, or None if unset.
        """
        return self.pos

    def get_flux_label(self, use_tex=False):
        """Return the empty flux label used by the base class.

        Args:
            use_tex (bool): Accepted for compatibility with subclass labels; unused.

        Returns:
            str: Empty string.
        """
        return ""

    def get_position_label(self, use_tex=False):
        """Return the empty position label used by the base class.

        Args:
            use_tex (bool): Accepted for compatibility with subclass labels; unused.

        Returns:
            str: Empty string.
        """
        return ""

    def _get_inputs(self, spectrum):
        """Read positions, fluxes and flux errors from another sampled spectrum.

        Args:
            spectrum (SampledSpectrum): Spectrum to read.

        Returns:
            tuple: Positions, fluxes and flux errors, without copying.
        """
        return spectrum.get_positions(), spectrum._get_fluxes(), spectrum._get_flux_errors()

    @staticmethod
    def _sample_flux(caller_class, coefficients, design_matrix):
        """Project coefficients onto the samples of a design matrix.

        Args:
            caller_class (type): Calling class, used to select the mismatch message.
            coefficients (numpy.ndarray): Coefficient vector of length n_bases.
            design_matrix (numpy.ndarray): Matrix of shape (n_bases, n_samples).

        Returns:
            numpy.ndarray or float: Flux vector of length n_samples, or scalar NaN
            for an empty coefficient array.

        Raises:
            ValueError: A non-empty coefficient vector has a different length from
                the number of design-matrix rows.
        """
        if coefficients.shape[0] != 0 and coefficients.shape[0] != design_matrix.shape[0]:
            error_message = ''
            if caller_class.__name__ == 'SingleSyntheticPhotometry':
                error_message += "Are you sure the input spectra and the photometric systems match? "
            else:
                error_message += "Please make sure you're using the correct input files and configuration (release). "
            error_message += (f"Coefficients length ({coefficients.shape[0]}) doesn't match the design matrix "
                              f"dimension ({design_matrix.shape[0]}).")
            raise ValueError(error_message)
        if isinstance(coefficients, ndarray) and coefficients.size > 0:
            return coefficients @ design_matrix
        return nan

    @staticmethod
    def _sample_error(design_cov_element, t_design_matrix, standard_deviation):
        """Calculate sample errors from a projected coefficient covariance.

        Args:
            design_cov_element (numpy.ndarray or float): design_matrix.T @ covariance,
                with shape (n_samples, n_bases), or scalar NaN.
            t_design_matrix (numpy.ndarray): Transposed design matrix, with shape
                (n_samples, n_bases).
            standard_deviation (float): Solution standard deviation, applied after
                taking the square root of the projected variance.

        Returns:
            numpy.ndarray or float: Flux errors of length n_samples, or
            scalar NaN when design_cov_element is NaN.

        Raises:
            TypeError: design_cov_element is neither a NumPy array nor scalar NaN.
        """
        if isinstance(design_cov_element, ndarray):
            return np.sqrt(
                np.sum(np.multiply(design_cov_element, t_design_matrix), axis=1)) * standard_deviation
        elif np.isnan(design_cov_element):
            return float('NaN')
        else:
            raise TypeError('Covariance must be either a NumPy array or nan.')

    @staticmethod
    def _sample_covariance(design_cov_element, design_matrix):
        """Given the covariance matrix and a design matrix containing the evaluation
        of each basis function at the positions corresponding to the samples, this
        method computes the covariance matrix of the sampled spectrum.

        Args:
            design_cov_element (numpy.ndarray): design_matrix.T @ covariance,
                with shape (n_samples, n_bases).
            design_matrix (numpy.ndarray): Matrix of shape (n_bases, n_samples).

        Returns:
            numpy.ndarray: Matrix of shape (n_samples, n_samples). No solution
            standard-deviation factor is applied here.
        """
        return design_cov_element @ design_matrix
