import unittest

from gaiaxpy.core.nature import PLANCK, C
from gaiaxpy.core.satellite import TELESCOPE_PUPIL_AREA, BP_WL, RP_WL, BANDS
from gaiaxpy.core.server import gaia_server, data_release


class TestConfig(unittest.TestCase):

    def test_nature(self):
        self.assertEqual(PLANCK, 6.62607004E-34)
        self.assertEqual(C, 2.99792458E8)

    def test_satellite(self):
        self.assertEqual(TELESCOPE_PUPIL_AREA, 0.7278)
        self.assertEqual(BP_WL[0], 330)
        self.assertEqual(BP_WL[1], 643)
        self.assertEqual(RP_WL[0], 635)
        self.assertEqual(RP_WL[1], 1020)
        self.assertEqual(BANDS.bp, 'bp')
        self.assertEqual(BANDS.rp, 'rp')

    def test_server(self):
        self.assertEqual(gaia_server, 'https://gea.esac.esa.int/')
        self.assertEqual(data_release, 'Gaia DR3')
