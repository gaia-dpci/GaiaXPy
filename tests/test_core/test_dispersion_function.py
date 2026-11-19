import numpy as np
import numpy.testing as npt
import pytest

from gaiaxpy import pwl_to_wl, wl_to_pwl, pwl_range, wl_range
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.satellite import BANDS, BP_WL_DR3, RP_WL_DR3


@pytest.mark.parametrize('release', RELEASES)
def test_validate_pwl_to_wl(release):
    for band in BANDS:
        # Only run assertion where the dispersion function is well-defined.
        pwl = np.linspace(5, 54, 61)
        wl = pwl_to_wl(band, pwl, release=release)
        # Now revert the transformation
        back_to_pwl = wl_to_pwl(band, wl, release=release)
        npt.assert_allclose(back_to_pwl, pwl, rtol=1e-5)


@pytest.mark.parametrize('release', RELEASES)
def test_dispersion_functions_accept_scalar_list_and_array(release):
    scalar_wl = pwl_to_wl(BANDS.bp, 10.0, release=release)
    assert isinstance(scalar_wl, float)

    list_wl = pwl_to_wl(BANDS.bp, [10.0, 11.0], release=release)
    assert isinstance(list_wl, np.ndarray)
    assert list_wl.shape == (2,)

    array_pwl = wl_to_pwl(BANDS.bp, np.asarray(list_wl), release=release)
    npt.assert_allclose(array_pwl, [10.0, 11.0], rtol=1e-5)


def test_release_specific_ranges():
    bp_dr3_range = wl_range(BANDS.bp, release=RELEASES.dr3)
    assert [bp_dr3_range.low, bp_dr3_range.high] == [BP_WL_DR3.low, BP_WL_DR3.high]
    rp_dr3_range = wl_range(BANDS.rp, release=RELEASES.dr3)
    assert [rp_dr3_range.low, rp_dr3_range.high] == [RP_WL_DR3.low, RP_WL_DR3.high]

    for release in RELEASES:
        for band in BANDS:
            assert len(pwl_range(band, release=release)) == 2
