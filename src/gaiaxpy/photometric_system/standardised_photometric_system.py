"""Represent filters that apply configured per-band flux-bias offsets.
"""

from .internal_photometric_system import InternalPhotometricSystem


class StandardisedPhotometricSystem(InternalPhotometricSystem):
    """Load a filter with per-band flux-bias corrections."""

    def __init__(self, name, is_builtin, release, config_file=None):
        """Load the selected filter through InternalPhotometricSystem.

        Args:
            name (str): Base system name.
            is_builtin (bool): Whether the filter is bundled with GaiaXPy.
            release (str): Gaia release, 'dr3'; a release must be supplied.
            config_file (str, pathlib.Path, mapping or None): Additional-filter
                selection path or snapshot; None uses the default selection path.

        Notes:
            Filter lookup, metadata validation and configuration-loading errors are
            reported to the caller as described by InternalPhotometricSystem.
        """
        super().__init__(name, is_builtin=is_builtin, release=release, config_file=config_file)
        # Offset loading is handled by InternalPhotometricSystem and must dispatch by file format.

    def standardised_system_flux_correction(self, flux):
        """Add the configured per-band offsets to flux.

        Args:
            flux (numpy.ndarray): Fluxes with bands along the final dimension.

        Returns:
            numpy.ndarray: Corrected fluxes, using NumPy broadcasting.
        """
        flux_corr = flux + self.offsets
        return flux_corr

    def standardised_system_error_correction(self, flux, error):
        """Scale flux errors by the absolute corrected-to-original flux ratio.

        Args:
            flux (numpy.ndarray): Original, uncorrected fluxes.
            error (numpy.ndarray): Corresponding flux errors.

        Returns:
            numpy.ndarray: error * abs((flux + offsets) / flux). Zero flux follows
            NumPy's division behaviour and can produce non-finite values.
        """
        eef = (flux + self.offsets) / flux
        eef = abs(eef)
        flux_error_corr = error * eef
        return flux_error_corr
