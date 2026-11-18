"""Represent filters that leave synthetic fluxes and flux errors unchanged."""
from .internal_photometric_system import InternalPhotometricSystem


class RegularPhotometricSystem(InternalPhotometricSystem):
    """Load a photometric system without flux-bias standardisation."""

    def __init__(self, name, is_builtin, release=None, config_file=None):
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
        super().__init__(name, is_builtin, release=release, config_file=config_file)

    def standardised_system_flux_correction(self, flux):
        """Return flux unchanged, without making a copy."""
        return flux

    def standardised_system_error_correction(self, flux, error):
        """Return error unchanged; flux is unused and no copy is made."""
        return error
