import numpy as np
from numpy import linalg as LA

_sqrt2 = np.sqrt(2.)


class HermiteDer():
    """
    Calculate zero-points of 1st and 2nd derivative of linear combination of Hermite functions.
    """

    def __init__(self, tm, n, n1, coeff):
        """
        Initialise.
        
        Args:
            tm (ndarray): 2D array containing bases transformation matrix.
            n (int): Number of bases.
            n1 (int): Number of relevant bases.
            coeff (ndarray): 1D array containing the coefficients multiplying the basis functions in the
                continuous representation.
        """

        self.n = n
        coeff[n1:] = 0.
        self.coeff = coeff
        self.bt = tm  # bases_transformation
        self.coeffbt = self.coeff.dot(self.bt)

    def get_roots_firstder(self):
        """
        Calculate zero-points of 1st derivative.
        
        Returns:
            ndarray: 1D array of zero-points.
        """

        N = self.n
        coeff1 = np.r_[self.coeffbt, [0]]

        D = np.zeros((N + 1, N + 1))
        R = np.arange(0, N)
        D[R + 1, R] = np.sqrt(R + 1) / _sqrt2
        D[R, R + 1] = -np.sqrt(R + 1) / _sqrt2

        # 1st derivative coefficients:
        coeffder = D.dot(coeff1)

        # b - matrix to calculate zeropoints
        b = np.zeros((N, N))
        R1 = np.arange(0, N - 1)
        b[R1 + 1, R1] = np.sqrt(R1 + 1) / _sqrt2
        b[R1, R1 + 1] = np.sqrt(R1 + 1) / _sqrt2
        b[N - 1, R] -= np.sqrt(N / 2.) * coeffder[:-1] / coeffder[-1]

        eigval = LA.eigvals(b)

        # 1st derivative zeropoints = extrema in spectrum
        roots = np.sort(eigval[np.isreal(eigval)].real)

        return roots  # roots have to be rescaled to pwl

    def get_roots_secondder(self):
        """
        Calculate zero-points of 2nd derivative.
        
        Returns:
            ndarray: 1D array of zero-points.
        """

        # 2nd derivative : 1st method direct from spectrum coefficients
        N = self.n
        coeff2 = np.r_[self.coeffbt, [0, 0]]

        R = np.arange(0, N)

        D2 = np.diag(-0.5 - np.arange(N + 2), k=0)

        D2[R, R + 2] = 0.5 * np.sqrt((R + 2) * (R + 1))
        D2[R + 2, R] = 0.5 * np.sqrt((R + 2) * (R + 1))

        # 2nd derivative coefficients:
        coeffder2 = D2.dot(coeff2)

        # b2 - matrix to calculate zeropoints
        b2 = np.zeros((N + 1, N + 1))
        b2[R + 1, R] = np.sqrt(R + 1) / _sqrt2
        b2[R, R + 1] = np.sqrt(R + 1) / _sqrt2

        b2[N, np.arange(0, N + 1)] -= np.sqrt((N + 1) / 2.) * coeffder2[:-1] / coeffder2[-1]

        eigval2 = LA.eigvals(b2)

        roots2 = np.sort(eigval2[np.isreal(eigval2)].real)

        return roots2
