import numpy as np
import numpy.testing as npt
import pytest

from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.core.generic_functions import (_get_system_label, _extract_systems_from_data, validate_pwl_sampling,
                                            array_to_symmetric_matrix, correlation_to_covariance,
                                            get_matrix_size_from_lower_triangle)
from tests.files.paths import mean_spectrum_fits_file


@pytest.fixture
def array():
    yield np.array([1, 2, 3, 4, 5, 6])


@pytest.fixture
def size():
    yield 3


def test_get_system_label():
    assert _get_system_label('Els_Custom_W09_S2') == 'ElsCustomW09S2'
    assert _get_system_label('DECam') == 'Decam'
    assert _get_system_label('Els_Custom_W09_S2') == 'ElsCustomW09S2'
    assert _get_system_label('Euclid_VIS') == 'EuclidVis'
    assert _get_system_label('Gaia_2') == 'Gaia2'
    assert _get_system_label('Gaia_DR3_Vega') == 'GaiaDr3Vega'
    assert _get_system_label('Halpha_Custom_AB') == 'HalphaCustomAb'
    assert _get_system_label('H_Custom') == 'HCustom'
    assert _get_system_label('Hipparcos_Tycho') == 'HipparcosTycho'
    assert _get_system_label('HST_ACSWFC') == 'HstAcswfc'
    assert _get_system_label('HST_WFC3UVIS') == 'HstWfc3uvis'
    assert _get_system_label('HST_WFPC2') == 'HstWfpc2'
    assert _get_system_label('IPHAS') == 'Iphas'
    assert _get_system_label('JKC') == 'Jkc'
    assert _get_system_label('JPAS') == 'Jpas'
    assert _get_system_label('JPLUS') == 'Jplus'
    assert _get_system_label('JWST_NIRCAM'), 'JwstNircam'
    assert _get_system_label('PanSTARRS1'), 'Panstarrs1'
    assert _get_system_label('Pristine'), 'Pristine'
    assert _get_system_label('SDSS'), 'Sdss'
    assert _get_system_label('Sky_Mapper'), 'SkyMapper'
    assert _get_system_label('Stromgren'), 'Stromgren'
    assert _get_system_label('WFIRST') == 'Wfirst'


def test_extract_systems_from_data():
    expected_output = ['Wfirst', 'HstWfc3uvis', 'GaiaDr3Vega', 'ElsCustomW09S2']
    phot_list = [PhotometricSystem.WFIRST, PhotometricSystem.HST_WFC3UVIS, PhotometricSystem.Gaia_DR3_Vega,
                 PhotometricSystem.Els_Custom_W09_S2]
    photometry = generate(mean_spectrum_fits_file, photometric_system=phot_list, save_file=False)
    assert _extract_systems_from_data(photometry) == expected_output
    assert _extract_systems_from_data(photometry, photometric_system=phot_list) == expected_output


def test_validate_pwl_sampling_upper_limit():
    sampling = np.linspace(0, 71, 300)
    with pytest.raises(ValueError):
        validate_pwl_sampling(sampling)


def test_validate_pwl_sampling_lower_limit():
    sampling = np.linspace(-11, 70, 300)
    with pytest.raises(ValueError):
        validate_pwl_sampling(sampling)


def test_validate_pwl_sampling_len_zero():
    sampling = np.linspace(0, 0, 0)
    with pytest.raises(ValueError):
        validate_pwl_sampling(sampling)


def test_validate_pwl_sampling_none():
    sampling = None
    with pytest.raises(ValueError):
        validate_pwl_sampling(sampling)


def test_validate_pwl_sampling():
    sampling = np.array([0.3, 0.2, 0.5])
    with pytest.raises(ValueError):
        validate_pwl_sampling(sampling)


def test_correlation_to_covariance():
    _array = np.random.random(21)
    error = np.random.random(7)
    cov = correlation_to_covariance(_array, error, 1.0)
    npt.assert_allclose(cov, cov.T, rtol=1e-8)  # Check that the matrix is symmetric


def test_get_matrix_size():
    assert get_matrix_size_from_lower_triangle(np.ones(6)) == 4
    assert get_matrix_size_from_lower_triangle(np.ones(10)) == 5
    assert get_matrix_size_from_lower_triangle(np.ones(15)) == 6
    assert get_matrix_size_from_lower_triangle(np.ones(21)) == 7


def test_array_to_symmetric_matrix_type(array, size):
    assert isinstance(array_to_symmetric_matrix(array, size), np.ndarray)


def test_array_to_symmetric_matrix_values(size):
    _array = np.array([4, 5, 6])
    expected_symmetric = np.array([[1., 4., 5.], [4., 1., 6.], [5., 6., 1.]])
    assert (array_to_symmetric_matrix(_array, size) == expected_symmetric).all()


def test_array_to_symmetric_matrix_mismatching(array):
    with pytest.raises(ValueError):
        array_to_symmetric_matrix(array, 2)


def test_array_to_symmetric_matrix_negative_size(array):
    with pytest.raises(ValueError):
        array_to_symmetric_matrix(array, -1)
