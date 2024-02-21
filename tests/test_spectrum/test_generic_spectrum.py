from gaiaxpy.spectrum.generic_spectrum import Spectrum


def test_spectrum_init():
    source_id = 5626132279854336
    spectrum = Spectrum(source_id)
    assert isinstance(spectrum, Spectrum)
    assert spectrum.get_source_id() == source_id
