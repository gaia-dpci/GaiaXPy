from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.xp_spectrum import XpSpectrum


def test_init_get():
    spectrum = XpSpectrum(1634280312200704768, BANDS.bp)
    assert isinstance(spectrum, XpSpectrum)
    assert spectrum.get_xp() == BANDS.bp
