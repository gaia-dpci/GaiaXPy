from os.path import basename, join

import numpy as np
import numpy.testing as npt
import pytest
from numpy import ndarray

from gaiaxpy.config.paths import filters_path
from gaiaxpy.core.config import get_file, load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.generator.internal_photometric_system import InternalPhotometricSystem


@pytest.fixture(scope='module')
def system_label():
    system = InternalPhotometricSystem('JKC')
    yield system.get_system_label()


def test_get_file():
    _system = 'test'
    bp_model = 'v375wi'
    rp_model = 'v142r'
    file_path = get_file('filter', 'filter', _system, bp_model, rp_model)
    assert file_path == join(filters_path, basename(file_path))


def test_load_xpsampling_from_csv_type(system_label):
    xp_sampling = load_xpsampling_from_xml(system=system_label)
    assert isinstance(xp_sampling, dict)


def test_load_xpmerge_from_xml_types(system_label):
    xp_sampling_grid, xp_merge = load_xpmerge_from_xml(system=system_label)
    assert isinstance(xp_merge, dict)
    assert isinstance(xp_sampling_grid, np.ndarray)


@pytest.mark.parametrize('system,offset', [('JKC_Std', np.array([2.44819e-19, 4.62320e-20, 1.81103e-20, 2.15027e-20,
                                                                 1.73864e-20])),
                                           ('SDSS_Std', np.array([1.05000e-31, 2.47850e-32, 3.49926e-32, 3.80023e-32,
                                                                  3.23519e-32])),
                                           ('Stromgren_Std', np.zeros(3))])
def test_load_xpoffset(system, offset):
    # Standard system has got an offset file
    _system = InternalPhotometricSystem(system)
    assert isinstance(_system.get_offsets(), ndarray)
    npt.assert_array_equal(_system.get_offsets(), offset)
