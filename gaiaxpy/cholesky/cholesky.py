from numpy import diag, dot, identity
from scipy.linalg import cholesky, solve_triangular
from gaiaxpy.input_reader import InputReader


def __get_inv_cholesky_decomp_lower(xp_errors, xp_correlation_matrix):
    L = cholesky(xp_correlation_matrix, lower=True)
    # Invert lower triangular matrix.
    ncoeffs = len(L)
    L_inv = solve_triangular(L, identity(ncoeffs), lower=True)
    # Matrix of inverse errors.
    E_inv = diag(1.0 / xp_errors)
    return dot(L_inv, E_inv)


def get_inverse_covariance_matrix(input_object=None, band=None):
    band = band.lower()
    parsed_input_data, extension = InputReader(input_object, cholesky)._read()
    xp_errors = parsed_input_data[f'{band}_coefficient_errors'].iloc[0]
    xp_correlation_matrix = parsed_input_data[f'{band}_coefficient_correlations'].iloc[0]
    L_inv = __get_inv_cholesky_decomp_lower(xp_errors, xp_correlation_matrix)
    return dot(L_inv.T, L_inv)

def get_chi2(residuals, L_inv):
    x = dot(L_inv.T, residuals)
    return dot(x.T, x)
