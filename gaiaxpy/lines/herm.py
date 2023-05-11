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
        coeff1 = np.r_[self.coeff_bt, [0]]

        _D = np.zeros((_N + 1, _N + 1))
        # Fill in the upper triangular part of _D
        for r in range(_N):
            _D[r + 1, r] = np.sqrt(r + 1) / _sqrt2
            _D[r, r + 1] = -np.sqrt(r + 1) / _sqrt2

        # 1st derivative coefficients:
        coeff_der = _D.dot(coeff1)

        # b - matrix to calculate zero-points
        b = np.zeros((_N, _N))
        # Fill in the upper triangular part of b
        for r in range(_N - 1):
            b[r + 1, r] = np.sqrt(r + 1) / _sqrt2
            b[r, r + 1] = np.sqrt(r + 1) / _sqrt2
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
        coeff2 = np.r_[self.coeff_bt, [0, 0]]

        _D2 = np.diag(-0.5 - np.arange(_N + 2), k=0)
        for r in range(_N):
            _D2[r, r + 2] = 0.5 * np.sqrt((r + 2) * (r + 1))
            _D2[r + 2, r] = 0.5 * np.sqrt((r + 2) * (r + 1))

        # 2nd derivative coefficients:
        coeff_der2 = _D2.dot(coeff2)

        # b2 - matrix to calculate zero-points
        b2 = np.zeros((_N + 1, _N + 1))
        for r in range(_N):
            b2[r + 1, r] = np.sqrt(r + 1) / _sqrt2
            b2[r, r + 1] = np.sqrt(r + 1) / _sqrt2

        b2[_N, np.arange(0, _N + 1)] -= np.sqrt((_N + 1) / 2.) * coeff_der2[:-1] / coeff_der2[-1]

        eigval2 = eigvals(b2)

        roots2 = np.sort(eigval2[np.isreal(eigval2)].real)

        return roots2
