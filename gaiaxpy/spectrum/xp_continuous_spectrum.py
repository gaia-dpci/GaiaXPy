"""
xp_continuous_spectrum.py
====================================
Module to represent a BP/RP continuous spectrum.
"""

from .xp_spectrum import XpSpectrum
from .utils import _list_to_array
import numpy as np
from gaiaxpy.core.satellite import BANDS

class XpContinuousSpectrum(XpSpectrum):
    """
    A Gaia BP/RP spectrum represented as a continuous function defined as
    the sum of a set of bases functions multiplied by a set of coefficient.
    This definition is the result of a least squares fit. Covariance and
    standard deviation for the least square solution are also part of the
    continuous spectrum definition to allow estimating errors.
    """

    def __init__(self,
                 source_id,
                 xp,
                 coefficients,
                 covariance,
                 standard_deviation):
        """"
        Initialise XP continuous spectrum.

        Args:
            source_id (str): Source identifier.
            xp (str): Gaia photometer, can be either 'bp' or 'rp'.
            coefficients (ndarray): 1D array containing the coefficients
                multiplying the basis functions.
            covariance (ndarray): 2D array containing the covariance of the
                least squares solution.
            standard_deviation (float): Standard deviation of the least
                squares solution.
        """
        XpSpectrum.__init__(self, source_id, xp)
        self.coefficients = coefficients
        self.covariance = covariance
        self.standard_deviation = standard_deviation
        self.basis_function_id = {BANDS.bp: 56, BANDS.rp: 57}

    def get_coefficients(self):
        """
        Get the coefficients associated with the spectrum.

        Returns:
            ndarray: The 1D array of the coefficients multiplying the basis functions.
        """
        return self.coefficients

    def get_covariance(self):
        """
        Get the covariance associated with the spectrum.

        Returns:
            ndarray: The 2D array of the covariance matrix.
        """
        return self.covariance

    def get_standard_deviation(self):
        """
        Get the standard deviation associated with the spectrum.

        Returns:
            float: The standard deviation of the least squares solution.
        """
        return self.standard_deviation

    def _spectrum_to_dict(self): #_archive_format
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
        n = self.coefficients.size
        D = np.sqrt(np.diag(self.covariance))
        D_inv = np.diag(1.0 / D)
        correlation_matrix = np.matmul(np.matmul(D_inv, self.covariance), D_inv)
        return {
            'source_id': self.source_id,
            'xp': self.xp.upper(),
            'standard_deviation': self.standard_deviation,
            'coefficients': _list_to_array(self.coefficients),
            'coefficient_correlations': _list_to_array(_extract_lower_triangle(correlation_matrix)),
            'coefficient_errors': _list_to_array(D),
            'n_parameters': len(self.coefficients),
            'basis_function_id': self.basis_function_id[self.xp]
        }

def _extract_lower_triangle(matrix):
    '''
    Extract the lower triangle of the matrix without including the diagonal.
    '''
    # Get the indices
    indices = np.tril_indices(matrix.shape[0], k=-1)
    values = []
    for i, j in zip(indices[0], indices[1]):
        values.append(matrix[i][j])
    return values
