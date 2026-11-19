"""Convert continuous BP/RP mean spectra to samples on a pseudo-wavelength grid.

The public entry point is gaiaxpy.convert. This package selects the configured
basis functions, evaluates each photometer separately and prepares the sampled
fluxes, flux errors and optional correlations for output.
"""
