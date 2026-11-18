import builtins
from pathlib import Path
from shutil import copyfile

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import PhotometricSystem
from gaiaxpy.colour_equation import xp_filter_system_colour_equation as colour_equation
from gaiaxpy.core.generic_functions import mag_to_flux


@pytest.fixture
def photometry():
    data = {'source_id': [42, 7]}
    for system in [PhotometricSystem.DR3_JKC_Std]:
        label = system.get_system_full_label()
        for band, zp in zip(system.get_bands(), system.get_zero_points()):
            magnitudes = [10., 12.]
            fluxes = [mag_to_flux(mag, zp) for mag in magnitudes]
            data[f'{label}_mag_{band}'] = magnitudes
            data[f'{label}_flux_{band}'] = fluxes
            data[f'{label}_flux_error_{band}'] = np.array(fluxes) * 0.01
    return pd.DataFrame(data)


@pytest.fixture
def misleading_files(tmp_path, monkeypatch):
    original = Path(colour_equation.colour_equation_dir)
    for filename in ['DR3_JkcStd_colour_eq.yaml', 'DR3_SdssStd_colour_eq.yaml']:
        copyfile(original / filename, tmp_path / filename)
        # Deliberately mislabel a DR3 equation as DR4: the release restriction
        # must reject it before its contents can be read.
        copyfile(original / filename, tmp_path / filename.replace('DR3_', 'DR4_'))
    monkeypatch.setattr(colour_equation, 'colour_equation_dir', tmp_path)
    return tmp_path


def test_mixed_systems_correct_only_dr3(mocker, photometry, misleading_files):
    original = photometry.copy(deep=True)
    open_file = mocker.patch.object(colour_equation, 'open', create=True, wraps=builtins.open)
    actual = colour_equation.apply_colour_equation(
        photometry, [PhotometricSystem.DR3_JKC_Std], save_file=False)

    # B-V is zero, so the JKC U correction is the polynomial's constant term.
    np.testing.assert_allclose(actual['DR3_JkcStd_mag_U'], [9.9118522108, 11.9118522108], rtol=0, atol=1e-12)
    corrected_columns = {'DR3_JkcStd_mag_U', 'DR3_JkcStd_flux_U', 'DR3_JkcStd_flux_error_U'}
    for column in corrected_columns:
        assert not actual[column].equals(original[column])
    unchanged = [column for column in original if column not in corrected_columns]
    pdt.assert_frame_equal(actual[unchanged], original[unchanged])
    pdt.assert_frame_equal(photometry, original)
    open_file.assert_called_once_with(misleading_files / 'DR3_JkcStd_colour_eq.yaml')
