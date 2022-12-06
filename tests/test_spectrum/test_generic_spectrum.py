import unittest

from gaiaxpy.spectrum.generic_spectrum import Spectrum


class TestSpectrum(unittest.TestCase):

    def test_spectrum_init(self):
        source_id = 5626132279854336
        spectrum = Spectrum(source_id)
        self.assertIsInstance(spectrum, Spectrum)
        self.assertEqual(spectrum.get_source_id(), source_id)
