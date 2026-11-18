import numpy as np
import pytest

from gaiaxpy.core.config import load_xpmerge_from_file, load_xpsampling_from_file
from gaiaxpy.core.config_dispatcher import GeneratorDispatcher
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.photometric_system.internal_photometric_system import InternalPhotometricSystem


@pytest.fixture(scope='module')
def system():
    system = InternalPhotometricSystem('JKC', is_builtin=True, release=RELEASES.dr3)
    yield system


def test_load_xpsampling_from_csv_type(system):
    config_file = GeneratorDispatcher().build(systems=[system], bp_model='v375wi', rp_model='v142r',
                                              release=RELEASES.dr3)
    xp_sampling = load_xpsampling_from_file(config_file)
    assert isinstance(xp_sampling, dict)


def test_load_xpmerge_from_xml_types(system):
    config_file = GeneratorDispatcher().build(systems=[system], bp_model='v375wi', rp_model='v142r',
                                              release=RELEASES.dr3)
    xp_sampling_grid, xp_merge = load_xpmerge_from_file(config_file)
    assert isinstance(xp_merge, dict)
    assert isinstance(xp_sampling_grid, np.ndarray)
