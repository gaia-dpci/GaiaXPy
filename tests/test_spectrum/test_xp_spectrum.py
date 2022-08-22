import unittest
from gaiaxpy.spectrum.xp_spectrum import XpSpectrum
from gaiaxpy.core.satellite import BANDS


class TestXpSpectrum(unittest.TestCase):

    def test_init_get(self):
        spectrum = XpSpectrum(1634280312200704768, BANDS.bp)
        self.assertIsInstance(spectrum, XpSpectrum)
        self.assertEqual(spectrum.get_xp(), BANDS.bp)
