"""Continuous BP/RP coefficients and their error information."""

from gaiaxpy.core.generic_functions import array_to_symmetric_matrix
from .utils import get_covariance_matrix
from .xp_spectrum import XpSpectrum


class XpContinuousSpectrum(XpSpectrum):
    """Hold the coefficient representation of one source in one photometer.

    The basis configuration is supplied separately when evaluating the spectrum.
    Coefficient covariance and the solution standard deviation are stored
    separately and used together when calculating sampled flux errors.
    """

    def __init__(self, source_id, xp, coefficients, covariance, standard_deviation):
        """Store the continuous-spectrum arrays without copying or reshaping them.

        Args:
            source_id (int or str): Source identifier.
            xp (str): BP or RP photometer.
            coefficients (numpy.ndarray): Coefficient vector of length n_bases.
            covariance (numpy.ndarray or float): Coefficient covariance matrix of
                shape (n_bases, n_bases), or NaN for an unavailable spectrum.
            standard_deviation (float): Standard deviation of the spectrum solution.
        """
        XpSpectrum.__init__(self, source_id, xp)
        self.coefficients = coefficients
        self.covariance = covariance
        self.standard_deviation = standard_deviation

    @classmethod
    def from_data_frame(cls, df, band):
        """Construct a spectrum from one row containing packed correlations.

        Args:
            df (pandas.Series): One source row with source_id and the selected band's
                n_parameters, coefficients, coefficient_correlations,
                coefficient_errors and standard_deviation fields. Band fields use
                the ``bp_`` or ``rp_`` prefix.
            band (str): Lowercase ``bp`` or ``rp``, used directly in field names.

        Returns:
            XpContinuousSpectrum: Coefficients and reconstructed covariance.

        Notes:
            Despite the method name, the input is a row, not a full table. The row's
            coefficient_correlations field is replaced with the full symmetric
            matrix before calculating covariance.
        """
        corr = array_to_symmetric_matrix(df[f'{band}_coefficient_correlations'], df[f'{band}_n_parameters'])
        df[f'{band}_coefficient_correlations'] = corr
        cov = get_covariance_matrix(df, band)
        return cls(df['source_id'], band, df[f'{band}_coefficients'], cov, df[f'{band}_standard_deviation'])

    @classmethod
    def get_units(cls):
        """Return the empty units mapping for a continuous coefficient representation.

        Returns:
            dict: Empty dictionary; units are not assigned to individual coefficients.
        """
        return dict()

    def get_coefficients(self):
        """Return the stored coefficient vector without conversion.

        Returns:
            numpy.ndarray: Value supplied at construction.
        """
        return self.coefficients

    def get_covariance(self):
        """Return the stored coefficient covariance without conversion.

        Returns:
            numpy.ndarray or float: Value supplied at construction.
        """
        return self.covariance

    def get_standard_deviation(self):
        """Return the stored solution standard deviation without conversion.

        Returns:
            float: Value supplied at construction.
        """
        return self.standard_deviation
