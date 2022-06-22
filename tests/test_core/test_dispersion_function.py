import unittest
import numpy as np
import numpy.testing as npt
import pandas as pd
from gaiaxpy.core import read_config_file, bp_pwl_range, bp_wl_range, \
                         rp_pwl_range, rp_wl_range, pwl_to_wl, wl_to_pwl
from gaiaxpy.core.satellite import BANDS

rtol = 1.e-5


class TestDispersionFunction(unittest.TestCase):

    def test_read_config_file(self):
        config_df = read_config_file()
        self.assertIsInstance(config_df, pd.DataFrame)
        self.assertEqual(len(config_df), 801)
        self.assertListEqual(list(config_df.columns), ['wl_nm', 'bp_pwl', 'rp_pwl'])


    def test_validate_pwl_to_wl(self):
        for band in BANDS:
            # Only run assertion where the dispersion function is well defined.
            pwl = np.linspace(5, 54, 61)
            wl = pwl_to_wl(band, pwl)
            # Now revert the transformation
            back_to_pwl = wl_to_pwl(band, wl)
            npt.assert_allclose(back_to_pwl, pwl, rtol=rtol)


    def test_bp_ranges(self):
        self.assertListEqual(bp_pwl_range, [51.1082, 14.83852])
        self.assertListEqual(bp_wl_range, [330, 643])


    def test_rp_ranges(self):
        self.assertListEqual(rp_pwl_range, [12.480039999999999, 48.86102])
        self.assertListEqual(rp_wl_range, [635, 1020])
