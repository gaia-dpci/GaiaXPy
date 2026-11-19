"""Generate synthetic photometry from continuous BP/RP mean spectra.

The public entry point is gaiaxpy.generate. Selected photometric systems supply
the passband integration matrices, zero points and standardisation settings.
Results contain magnitudes, fluxes and flux errors, with metadata identifying
the filter files and corrections used.
"""
