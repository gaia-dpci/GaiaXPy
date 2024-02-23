from gaiaxpy.core.nature import PLANCK, C
from gaiaxpy.core.satellite import TELESCOPE_PUPIL_AREA, BP_WL, RP_WL, BANDS
from gaiaxpy.core.server import gaia_server, data_release


def test_nature():
    assert PLANCK == 6.62607004E-34
    assert C == 2.99792458E8


def test_satellite():
    assert TELESCOPE_PUPIL_AREA == 0.7278
    assert BP_WL[0] == 330
    assert BP_WL[1] == 643
    assert RP_WL[0] == 635
    assert RP_WL[1] == 1020
    assert BANDS.bp == 'bp'
    assert BANDS.rp == 'rp'


def test_server():
    assert gaia_server == 'https://gea.esac.esa.int/'
    assert data_release == 'Gaia DR3'
