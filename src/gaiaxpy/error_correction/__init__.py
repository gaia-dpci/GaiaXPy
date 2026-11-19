"""Apply tabulated correction factors to synthetic-photometry flux errors.

The public entry point is gaiaxpy.apply_error_correction. Correction tables are
specific to a Gaia data release, system and passband. Factors depend on Gaia Vega
G magnitude; fluxes and magnitudes are left unchanged. This is separate from
the input coefficient correction and photometric-system standardisation.
"""
