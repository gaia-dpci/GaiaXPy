from numpy import diag, dot, identity
from scipy.linalg import cholesky, solve_triangular
from gaiaxpy.input_reader.input_reader import InputReader


def __get_dot_product(L_inv):
    return dot(L_inv.T, L_inv)

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
    xp_errors = parsed_input_data[f'{band}_coefficient_errors']
    xp_correlation_matrix = parsed_input_data[f'{band}_coefficient_correlations']
    L_inv_iterable = map(__get_inv_cholesky_decomp_lower, xp_errors, xp_correlation_matrix)
    output = list(map(__get_dot_product, L_inv_iterable))
    if len(output) > 1:
        return output
    elif len(output) == 1:
        return output[0]


def get_chi2(residuals, L_inv):
    x = dot(L_inv.T, residuals)
    return dot(x.T, x)
