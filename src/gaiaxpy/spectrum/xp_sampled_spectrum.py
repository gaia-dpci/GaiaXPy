"""Representation of a BP/RP sampled spectrum."""

from numbers import Number

import numpy as np

from .sampled_spectrum import SampledSpectrum
from .xp_spectrum import XpSpectrum
from ..core.generic_functions import is_array_empty, is_variable_empty, lower_correlation_from_covariance


class XpSampledSpectrum(XpSpectrum, SampledSpectrum):
    """BP or RP samples with optional covariance and solution standard deviation.

    Conversion normally evaluates these samples on a pseudo-wavelength grid.
    Direct constructors store the supplied arrays without checking their units.
    """

    def __init__(self, source_id, xp, pos=None, flux=None, flux_error=None, cov=None, stdev=None):
        """Store sample arrays and normalise empty values to None.

        Args:
            source_id (int or str): Source identifier.
            xp (str): BP or RP photometer.
            pos (numpy.ndarray or None): One-dimensional sample positions.
            flux (numpy.ndarray or None): Flux at each position.
            flux_error (numpy.ndarray or None): Flux error at each position.
            cov (numpy.ndarray or None): Square sample covariance matrix.
            stdev (float or None): Standard deviation.

        Notes:
            NumPy arrays are retained without copying. Missing or empty arrays are
            stored as None. n_samples is taken from pos when available.
        """
        XpSpectrum.__init__(self, source_id, xp)
        self.pos = pos
        self.n_samples = None if is_array_empty(self.pos) else len(self.pos)
        self.flux = None if is_array_empty(flux) else flux
        self.flux_error = None if is_array_empty(flux_error) else flux_error
        self.stdev = None if is_variable_empty(stdev) else stdev
        self.covariance = None if is_array_empty(cov) else cov

    @classmethod
    def from_data_frame(cls, df, sampling, band):
        """Construct a sampled spectrum from one source row.

        Args:
            df (pandas.Series or dict): Row containing source_id, flux, flux_error
                and cov. The cov field is required even when its value is None.
            sampling (numpy.ndarray): Positions corresponding to the row's samples.
            band (str): BP or RP photometer.

        Returns:
            XpSampledSpectrum: Stored samples. No standard deviation is supplied by
            this factory.

        Raises:
            KeyError: A required row field is missing.
        """
        return cls(df['source_id'], band, sampling, df['flux'], df['flux_error'], df['cov'])

    @classmethod
    def from_continuous(cls, continuous_spectrum, sampled_basis_functions, truncation=-1, with_correlation=False):
        """Evaluate coefficients and propagate their covariance onto a sample grid.

        Args:
            continuous_spectrum (XpContinuousSpectrum): Spectrum to evaluate. A
                populated coefficient vector requires a full covariance matrix.
            sampled_basis_functions (SampledBasisFunctions): Matrix with one row
                per basis function and one column per sample, and its sample grid.
            truncation (int): Recommended number of basis functions for this source
                and photometer: bp_n_relevant_bases for BP or rp_n_relevant_bases
                for RP, passed by convert when truncation=True. A non-positive
                value keeps all available basis functions.
            with_correlation (bool): Also calculate and retain the sample covariance
                needed to return correlations.

        Returns:
            XpSampledSpectrum: Fluxes and errors, or a spectrum containing
            only positions and identifiers if the coefficients are empty.

        Raises:
            ValueError: Either input object is missing, or coefficient and design
                matrix dimensions do not match.
            TypeError: A supplied covariance value is neither a NumPy array nor NaN.
        """
        if continuous_spectrum and sampled_basis_functions:
            coefficients = continuous_spectrum.get_coefficients()
            pos = sampled_basis_functions.get_sampling_grid()
            if is_array_empty(coefficients):
                return cls(continuous_spectrum.get_source_id(), continuous_spectrum.get_band(), pos)
            else:
                design_matrix = sampled_basis_functions.get_design_matrix()
                covariance = continuous_spectrum.get_covariance()
                # Fail fast if covariance is not of the expected type
                if not isinstance(covariance, np.ndarray) and not np.isnan(covariance):
                    raise TypeError('Covariance must be either a NumPy array or nan.')
                # Truncate relevant inputs if necessary
                coefficients, covariance, design_matrix = cls.apply_truncation(coefficients, covariance,
                                                                               design_matrix, truncation)
                stdev = continuous_spectrum.get_standard_deviation()
                # Generate sampled outputs
                flux = SampledSpectrum._sample_flux(SampledSpectrum.__class__, coefficients, design_matrix)
                t_design_matrix = design_matrix.T
                shared_cov_element = t_design_matrix @ covariance
                flux_error = SampledSpectrum._sample_error(shared_cov_element, t_design_matrix, stdev)
                cov = SampledSpectrum._sample_covariance(shared_cov_element,
                                                         design_matrix) if with_correlation else None
                return cls(continuous_spectrum.get_source_id(), continuous_spectrum.get_band(), pos, flux, flux_error,
                           cov, stdev)
        else:
            raise ValueError('Either the continuous spectrum or the sampled basis functions argument is empty.')

    @classmethod
    def apply_truncation(cls, coefficients, covariance, design_matrix, truncation: int) -> tuple:
        """Truncate coefficients, covariance entries and basis rows according to the number of relevant bases.

        Args:
            coefficients (numpy.ndarray): Coefficient vector.
            covariance (numpy.ndarray): Square coefficient covariance matrix.
            design_matrix (numpy.ndarray): Basis-by-sample matrix.
            truncation (int): This source's bp_n_relevant_bases or
                rp_n_relevant_bases value for the photometer being processed when
                truncation is enabled. Retain that many leading basis functions.
                A non-positive count keeps all available basis functions.

        Returns:
            tuple: Coefficients, covariance and design matrix, in that order. Slices
            can share memory with the inputs.
        """
        if isinstance(truncation, Number) and truncation > 0:
            coefficients = coefficients[:truncation]
            covariance = covariance[:truncation, :truncation]
            design_matrix = design_matrix[:truncation][:]
        return coefficients, covariance, design_matrix

    @classmethod
    def from_sampled(cls, source_id, band, pos, flux, flux_error, cov=None):
        """Construct a spectrum from already sampled values.

        Args:
            source_id (int or str): Source identifier.
            band (str): BP or RP photometer.
            pos (numpy.ndarray): One-dimensional sample positions.
            flux (numpy.ndarray): Flux vector.
            flux_error (numpy.ndarray): Flux error vector.
            cov (numpy.ndarray or None): Optional square covariance matrix.

        Returns:
            XpSampledSpectrum: Samples stored without resampling. The solution
            standard deviation remains unset.
        """
        return cls(source_id, band, pos, flux, flux_error, cov)

    def spectrum_to_tuple(self, with_correlation):
        """Arrange the sampled spectrum for conversion output.

        Args:
            with_correlation (bool): Append lower-triangle sample correlations and
                the solution standard deviation. Requires a populated covariance.

        Returns:
            tuple: source_id, uppercase photometer name, flux and flux_error;
            optionally followed by packed correlations and stdev. The correlation
            vector excludes the diagonal. Sample positions are returned separately
            by the calling operation.
        """
        if with_correlation:
            correlation = lower_correlation_from_covariance(self.covariance)
            return self.source_id, self.band.upper(), self.flux, self.flux_error, correlation, self.stdev

        return self.source_id, self.band.upper(), self.flux, self.flux_error

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

    def get_positions(self):
        """Return the stored sample positions without copying.

        Returns:
            numpy.ndarray or None: Stored one-dimensional array, or None if unset.
        """
        return self.pos

    def _get_covariance(self):
        """Return the stored sample covariance without copying.

        Returns:
            numpy.ndarray or None: Stored two-dimensional array, or None if unset.
        """
        return self.covariance

    @classmethod
    def get_units(cls):
        """Return the unit labels used for internal sampled-spectrum output.

        Returns:
            dict: Flux, flux_error and standard_deviation are labelled 'electron/s';
            positions are labelled 'pwl'. This method does not convert stored values.
        """
        return {'flux': 'electron/s', 'flux_error': 'electron/s', 'standard_deviation': 'electron/s', 'pos': 'pwl'}

    @classmethod
    def get_flux_label(cls, use_tex=False):
        """Return the plot label for flux in electrons per second.

        Args:
            use_tex (bool): Format the label for rendering with TeX.

        Returns:
            str: Label describing the plotted quantity.
        """
        return r'Flux [$\mathrm{e^-\,s^{-1}}$]' if use_tex else 'Flux [e-/s]'

    @classmethod
    def get_position_label(cls, use_tex=False):
        """Return the plot label for pseudo-wavelength.

        Args:
            use_tex (bool): Format the label for rendering with TeX.

        Returns:
            str: Label describing the plotted quantity.
        """
        return r'Pseudo\mbox{-}wavelength' if use_tex else 'Pseudo-wavelength'
