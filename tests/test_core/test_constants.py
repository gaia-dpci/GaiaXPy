from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.nature import PLANCK, C
from gaiaxpy.core.satellite import TELESCOPE_PUPIL_AREA, BP_WL_DR3, RP_WL_DR3, BANDS
from gaiaxpy.core.server import gaia_server, get_release_for_archive


def test_nature():
    assert PLANCK == 6.62607015E-34
    assert C == 2.99792458E8


def test_satellite():
    assert TELESCOPE_PUPIL_AREA == 0.7278
    assert BP_WL_DR3[0] == 330
    assert BP_WL_DR3[1] == 643
    assert RP_WL_DR3[0] == 635
    assert RP_WL_DR3[1] == 1020
    assert BANDS.bp == 'bp'
    assert BANDS.rp == 'rp'


def test_server():
    assert gaia_server == 'https://gea.esac.esa.int/'
    assert get_release_for_archive(RELEASES.dr3) == 'Gaia DR3'
