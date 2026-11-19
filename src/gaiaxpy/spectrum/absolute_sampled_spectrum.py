"""Representation of an absolute sampled spectrum."""

from numbers import Number

import numpy as np

from .sampled_spectrum import SampledSpectrum
from ..core.custom_errors import NoBandsAvailableError
from ..core.satellite import BANDS


class AbsoluteSampledSpectrum(SampledSpectrum):
    """Base for spectra calibrated onto the absolute system of wavelength and flux.
    Each spectrum is represented by a set of discrete measurements or samples.

    This constructor identifies available photometers and stores the common sampling
    grid. Subclasses evaluate and merge their contributions. A band is considered
    available when its continuous spectrum has a NumPy covariance array.
    """

    def __init__(self, source_id, xp_spectra, sampled_bases, merge, truncation=None, with_correlation=False):
        """Store the grid, merge weights and per-photometer truncation values.

        Args:
            source_id (int or str): Source identifier.
            xp_spectra (dict): Continuous spectra keyed by 'bp' and/or 'rp'.
            sampled_bases (dict): SampledBasisFunctions objects keyed by photometer,
                using the same output grid and basis-by-sample matrix layout.
            merge (dict): BP and RP weights on that output grid.
            truncation (dict or None): Recommended number of basis functions for
                each photometer, keyed by 'bp' and 'rp'. When truncation is enabled,
                the calling operation passes this source's bp_n_relevant_bases
                and rp_n_relevant_bases values. None or an empty dictionary uses
                all available basis functions, as does a missing or non-positive
                count for an individual photometer.
            with_correlation (bool): Retain projected covariance for correlations.

        Raises:
            NoBandsAvailableError: Neither supplied spectrum has a NumPy covariance
                array.

        Notes:
            This base constructor does not calculate fluxes or errors.
        """
        self.truncation = dict() if truncation is None else truncation
        self.available_bands = self.get_available_bands(xp_spectra)
        self.merge = merge
        self.with_correlation = with_correlation
        if not self.available_bands:
            raise NoBandsAvailableError()
        pos = sampled_bases[self.available_bands[0]].get_sampling_grid()
        SampledSpectrum.__init__(self, source_id, pos)
        self.pos = pos

    @staticmethod
    def get_available_bands(xp_spectra):
        """Find supplied photometers whose covariance is a NumPy array.

        Args:
            xp_spectra (dict): Objects exposing a covariance attribute, keyed by band.

        Returns:
            list[str]: Available keys in dictionary order. The check does not test
            array dimensions, contents or coefficient availability.
        """

        def __is_available_band(_xp_spectra, band):
            """Return whether the selected spectrum stores its covariance as a NumPy array."""
            return isinstance(_xp_spectra[band].covariance, np.ndarray)

        return [band for band in xp_spectra.keys() if __is_available_band(xp_spectra, band)]

    def generate_spectra(self, xp_spectra, sampled_bases, with_correlation):
        """Evaluate each available photometer before merging.

        Args:
            xp_spectra (dict): Continuous spectra keyed by photometer.
            sampled_bases (dict): Basis-by-sample matrices and grids for each band.
            with_correlation (bool): Include projected covariance and standard
                deviation in each band's result. This is later used to compute
                output correlations.

        Returns:
            dict: Per-band dictionaries containing xp_spectra, flux and flux_error,
                with cov and stdev added when requested. Flux errors include the solution
                standard deviation.
        """
        split_spectrum = {band: dict() for band in self.available_bands}
        for band in self.available_bands:
            band_truncation = self.truncation.get(band)
            split_spectrum[band]['xp_spectra'] = xp_spectra[band]
            stdev = split_spectrum[band]['xp_spectra'].get_standard_deviation()
            design_matrix = sampled_bases[band].get_design_matrix()
            spectra_covariance = split_spectrum[band]['xp_spectra'].get_covariance()
            coefficients = split_spectrum[band]['xp_spectra'].get_coefficients()
            # Apply truncation if necessary
            coefficients, design_matrix, spectra_covariance = AbsoluteSampledSpectrum.apply_truncation(band_truncation,
                                                                                                       coefficients,
                                                                                                       design_matrix,
                                                                                                       spectra_covariance)
            split_spectrum[band]['flux'] = self._sample_flux(self.__class__, coefficients, design_matrix)
            t_design_matrix = design_matrix.T
            shared_cov_element = t_design_matrix @ spectra_covariance
            split_spectrum[band]['flux_error'] = self._sample_error(shared_cov_element, t_design_matrix, stdev)
            if with_correlation:
                # Mathematically, sampling + merging of BP/RP spectra is a design matrix and thus cov_sampled = design @ cov_coeffs @ design.T
                if len(self.available_bands) == 2:
                    # D_merge is diagonal. Scale the rows of D_sampling @ C_coeff and the columns of D_sampling.T and
                    # reuse the same row scaling on D_sampling @ C_coeff.
                    # D_total = W @ design_matrix.T, where W is diagonal.
                    weights = self.merge[band]
                    covariance = self._sample_covariance(weights[:, None] * shared_cov_element, design_matrix * weights)
                else:
                    covariance = self._sample_covariance(shared_cov_element, design_matrix)
                split_spectrum[band]['cov'] = covariance * stdev ** 2
        return split_spectrum

    @staticmethod
    def apply_truncation(band_truncation, coefficients, design_matrix, spectra_covariance) -> tuple:
        """Slice one band's coefficient vector, design matrix and covariance together.

        Args:
            band_truncation (int or None): This source's bp_n_relevant_bases or
                rp_n_relevant_bases value for the photometer being processed when
                truncation is enabled. Retain that many leading basis functions.
                None or a non-positive count keeps all available basis functions.
            coefficients (numpy.ndarray): Coefficient vector.
            design_matrix (numpy.ndarray): Basis-by-sample matrix.
            spectra_covariance (numpy.ndarray): Square coefficient covariance.

        Returns:
            tuple: Coefficients, design matrix and covariance, in that order.
        """
        if isinstance(band_truncation, Number) and band_truncation > 0:
            design_matrix = design_matrix[:band_truncation][:]
            spectra_covariance = spectra_covariance[:band_truncation, :band_truncation]
            coefficients = coefficients[:band_truncation]
        return coefficients, design_matrix, spectra_covariance

    def __merge_output(self, split_spectrum):
        """Placeholder for subclass-specific output merging.

        Args:
            split_spectrum (dict): Per-band sampled results.

        Raises:
            NotImplementedError: Always; merging is provided by subclasses.
        """
        raise NotImplementedError('Method not implemented for base class.')

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

    @classmethod
    def get_units(cls):
        """Return the wavelength and flux unit labels for calibrated spectra.

        Returns:
            dict: 'nm' for positions and 'W.nm**-1.m**-2' for flux and flux_error.
            No conversion of stored values is performed.
        """
        return {'flux': 'W.nm**-1.m**-2', 'flux_error': 'W.nm**-1.m**-2', 'pos': 'nm'}

    @classmethod
    def get_flux_label(cls, use_tex=False):
        """Return the plot label for flux in W nm^-1 m^-2.

        Args:
            use_tex (bool): Format the label for rendering with TeX.

        Returns:
            str: Label describing the plotted quantity.
        """
        return r'Flux [$\mathrm{W\,nm^{-1}\,m^{-2}}$]' if use_tex else 'Flux [W nm^-1 m^-2]'

    @classmethod
    def get_position_label(cls, use_tex=False):
        """Return the plot label for wavelength in nanometres.

        Args:
            use_tex (bool): Format the label for rendering with TeX.

        Returns:
            str: Label describing the plotted quantity.
        """
        return r'Wavelength [$\mathrm{nm}$]' if use_tex else 'Wavelength [nm]'

    def merge_variables(self, split_spectrum):
        """Combine BP and RP sample values using the stored merge arrays.

        Args:
            split_spectrum (dict): BP and RP results containing flux and flux_error,
                plus cov when with_correlation is enabled.

        Notes:
            Stores the weighted flux sum in self.flux. Flux errors are combined in
            quadrature using squared weights. The sample covariance sums the
            weighted band contributions, assuming zero BP–RP cross-covariance.
        """
        merge = self.merge
        self.flux = np.add(np.multiply(split_spectrum[BANDS.bp]['flux'], merge[BANDS.bp]),
                           np.multiply(split_spectrum[BANDS.rp]['flux'], merge[BANDS.rp]))
        self.flux_error = np.sqrt(np.add(np.multiply(split_spectrum[BANDS.bp]['flux_error'] ** 2,
                                                     merge[BANDS.bp] ** 2),
                                         np.multiply(split_spectrum[BANDS.rp]['flux_error'] ** 2,
                                                     merge[BANDS.rp] ** 2)))
        if self.with_correlation:
            self.covariance = np.add(split_spectrum[BANDS.bp]['cov'], split_spectrum[BANDS.rp]['cov'])
