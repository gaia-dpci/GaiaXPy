import pytest

from gaiaxpy import PhotometricSystem
from gaiaxpy.generator.generator import _generate
from gaiaxpy.generator.multi_synthetic_photometry_generator import MultiSyntheticPhotometryGenerator
from tests.files.continuous import dr3_mean_spectra_csv_file


@pytest.mark.parametrize('name', ['bp_model', 'rp_model'])
def test_generate_rejects_removed_model_arguments(name):
    with pytest.raises(TypeError, match=f"unexpected keyword argument '{name}'"):
        _generate(dr3_mean_spectra_csv_file, PhotometricSystem.DR3_SDSS, save_file=False, **{name: None})


@pytest.mark.parametrize('name', ['bp_model', 'rp_model'])
def test_internal_generator_rejects_removed_model_arguments(name):
    with pytest.raises(TypeError, match=f"unexpected keyword argument '{name}'"):
        MultiSyntheticPhotometryGenerator([PhotometricSystem.DR3_SDSS], **{name: None})
