import numpy as np
from numpy.linalg import eigvals

_sqrt2 = np.sqrt(2.)


class HermiteDerivative:
    """
    Calculate zero-points of 1st and 2nd derivative of linear combination of Hermite functions.
    """

    def __init__(self, bases_transform_matrix, n_bases, n_rel_bases, coeff):
        """
        Initialise Hermite Derivative object.

        Args:
            bases_transform_matrix (ndarray): 2D array containing bases transformation matrix.
            n_bases (int): Number of bases.
            n_rel_bases (int): Number of relevant bases.
            coeff (ndarray): 1D array containing the coefficients multiplying the basis functions in the
                continuous representation.
        """

        self.n = n_bases
        coeff[n_rel_bases:] = 0.
        self.coeff = coeff
        self.bases_transform = bases_transform_matrix
        self.coeff_bt = self.coeff.dot(self.bases_transform)

    def get_roots_first_der(self):
        """
        Calculate zero-points of 1st derivative.

        Returns:
            ndarray: 1D array of zero-points.
        """
        _N = self.n
        _D = np.diag(np.sqrt(np.arange(1, _N + 1)), k=-1)
        _D = _D + _D.T * -1
        # 1st derivative coefficients:
        coeff_der = _D.dot(np.r_[self.coeff_bt, [0]])
        # b - matrix to calculate zero-points
        r = np.arange(_N - 1)
        b = np.zeros((_N, _N))
        b[r + 1, r] = np.sqrt(r + 1) / _sqrt2
        b = b + b.T
        # Fill in the last row of b
        b[_N - 1, :] -= np.sqrt(_N / 2.) * coeff_der[:-1] / coeff_der[-1]
        _eigval = eigvals(b)
        # 1st derivative zero-points = extrema in spectrum
        return np.sort(_eigval[np.isreal(_eigval)].real)

    def get_roots_second_der(self):
        """
        Calculate zero-points of 2nd derivative.

        Returns:
            ndarray: 1D array of zero-points.
        """

        # 2nd derivative : 1st method direct from spectrum coefficients
        _N = self.n
        r = np.arange(_N)
        _D2 = np.zeros((_N + 2, _N + 2))
        _D2[r, r + 2] = 0.5 * np.sqrt((r + 2) * (r + 1))
        _D2 = _D2 + _D2.T
        _D2 = _D2 + np.diag(-0.5 - np.arange(_N + 2), k=0)
        # 2nd derivative coefficients:
        coeff_der2 = _D2.dot(np.r_[self.coeff_bt, [0, 0]])
        # b2 - matrix to calculate zero-points
        b2 = np.zeros((_N + 1, _N + 1))
        b2[r + 1, r] = np.sqrt(r + 1) / _sqrt2
        b2 = b2 + b2.T
        b2[_N, np.arange(0, _N + 1)] -= np.sqrt((_N + 1) / 2.) * coeff_der2[:-1] / coeff_der2[-1]
        eigval2 = eigvals(b2)
        return np.sort(eigval2[np.isreal(eigval2)].real)
