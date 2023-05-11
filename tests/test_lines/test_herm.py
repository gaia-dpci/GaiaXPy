import unittest

import numpy as np
import numpy.testing as npt

from gaiaxpy.lines.herm import HermiteDer

n = 4
tm = np.ones((n, n))

roots1real = np.array([-2.22763054, -0.7096557, 0.10855341, 1.60398796])
roots2real = np.array([-2.79919062, -1.36826751, -0.27878957, 0.8772249, 2.34427792])


class TestHermites(unittest.TestCase):

    def test_get_roots(self):
        n1 = n
        coeff = np.arange(1, n + 1)
        hd = HermiteDer(tm, n, n1, coeff)
        roots1 = hd.get_roots_firstder()
        npt.assert_allclose(roots1, roots1real)
        roots2 = hd.get_roots_secondder()
        npt.assert_allclose(roots2, roots2real)

    def test_get_roots_trunc(self):
        n1 = 3
        coeff = np.arange(1, n + 1)
        hd = HermiteDer(tm, n, n1, coeff)
        roots1 = hd.get_roots_firstder()
        npt.assert_allclose(roots1, roots1real)
        roots2 = hd.get_roots_secondder()
        npt.assert_allclose(roots2, roots2real)
