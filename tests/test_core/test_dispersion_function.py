import unittest

import numpy as np
import numpy.testing as npt

from gaiaxpy import pwl_to_wl, wl_to_pwl
from gaiaxpy.core.satellite import BANDS

rtol = 1.e-5


class TestDispersionFunction(unittest.TestCase):

    def test_validate_pwl_to_wl(self):
        for band in BANDS:
            # Only run assertion where the dispersion function is well defined.
            pwl = np.linspace(5, 54, 61)
            wl = pwl_to_wl(band, pwl)
            # Now revert the transformation
            back_to_pwl = wl_to_pwl(band, wl)
            npt.assert_allclose(back_to_pwl, pwl, rtol=rtol)
