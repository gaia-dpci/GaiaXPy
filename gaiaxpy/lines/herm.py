import numpy as np
from numpy import linalg as LA

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
        self.bt = tm #bases_transformation
        self.coeffbt = self.coeff.dot(self.bt)
      
    def get_roots_firstder(self):
        """
        Calculate zero-points of 1st derivative.
        
        Returns:
            ndarray: 1D array of zero-points.
        """
   
        N = self.n
        coeff1 = np.r_[self.coeffbt,[0]]

        D = np.zeros((N+1,N+1))
        for i in np.arange(1,N+1):
            D[i,i-1] = np.sqrt(i)/np.sqrt(2.)
            D[i-1,i] =- np.sqrt(i)/np.sqrt(2.)

        # 1st derivative coefficients:
        coeffder = D.dot(coeff1)

        # b - matrix to calculate zeropoints
        b = np.zeros((N,N))

        for i in np.arange(1,N):
            b[i,i-1] = np.sqrt(i)/np.sqrt(2.)
            b[i-1,i] = np.sqrt(i)/np.sqrt(2.)

        for i in np.arange(0,N):
            b[N-1,i] -= np.sqrt(N/2.)*coeffder[i]/coeffder[-1]

        eigval = LA.eigvals(b)

        # 1st derivative zeropoints = extrema in spectrum
        roots = np.sort(eigval[np.isreal(eigval)].real)
   
        return roots # roots have to be rescaled to pwl

    def get_roots_secondder (self):
        """
        Calculate zero-points of 2nd derivative.
        
        Returns:
            ndarray: 1D array of zero-points.
        """
   
        # 2nd derivative : 1st method direct from spectrum coefficients
        N = self.n
        coeff2 = np.r_[self.coeffbt,[0,0]]
  
        D2 = np.zeros((N+2,N+2))
        for i in np.arange(0,N+2):
            D2[i,i] = 0.5 - i-1

        for i in np.arange(2,N+2):
            D2[i,i-2] = 0.5*np.sqrt(i*(i-1))
            D2[i-2,i] = 0.5*np.sqrt(i*(i-1))

        # 2nd derivative coefficients:
        coeffder2 = D2.dot(coeff2)

        # b2 - matrix to calculate zeropoints
        b2 = np.zeros((N+1,N+1))

        for i in np.arange(1,N+1):
            b2[i,i-1] = np.sqrt(i)/np.sqrt(2.)
            b2[i-1,i] = np.sqrt(i)/np.sqrt(2.)

        for i in np.arange(0,N+1):
            b2[N,i] -= np.sqrt((N+1)/2.)*coeffder2[i]/coeffder2[-1]

        eigval2 = LA.eigvals(b2)

        roots2 = np.sort(eigval2[np.isreal(eigval2)].real)

        return roots2
