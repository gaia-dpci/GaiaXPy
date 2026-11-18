"""Compute covariance inverses, inverse Cholesky factors and chi-squared values.

The matrix functions accept continuous BP/RP spectra through InputReader.
They divide coefficient errors by the corresponding photometer's standard
deviation before constructing the covariance used in these calculations.
get_chi2 applies a supplied inverse Cholesky factor to coefficient residuals.
"""
