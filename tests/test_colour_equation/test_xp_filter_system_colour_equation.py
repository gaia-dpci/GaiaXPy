import math

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest
from gaiaxpy import generate, PhotometricSystem
from gaiaxpy.colour_equation.xp_filter_system_colour_equation import apply_colour_equation
from gaiaxpy.core.generic_functions import cast_output
from gaiaxpy.file_parser.cast import _cast

from tests.files.paths import colour_eq_csv_file
from tests.test_colour_equation.colour_equation_paths import col_eq_sol_johnson_path


def get_mag_error(flux, flux_error):
    return 2.5 * flux_error / (flux * math.log(10))


@pytest.fixture(scope='module')
def sdss_std_cols():
    phot_system = PhotometricSystem.SDSS_Std
    label = phot_system.get_system_label()
    variables = ['mag', 'flux', 'flux_error']
    bands = ['u', 'g', 'r', 'i', 'z']
    sdss_std_cols = ['source_id'] + [f'{label}_{v}_{b}' for v in variables for b in bands]
    yield sdss_std_cols


def test_wrong_input_type():
    with pytest.raises(ValueError):
        _ = apply_colour_equation(colour_eq_csv_file)


@pytest.mark.parametrize('values', [[4154201362082430080, 2.235461e+01, np.nan, 1.975758e+01, 1.715846e+01,
                                     1.451727e+01, 4.838556e-32, -9.957407e-33, 4.524045e-31, 4.901128e-30,
                                     5.608559e-29, 8.698059e-32, 2.798101e-33, 1.464481e-31, 5.201447e-32,
                                     1.301941e-31],
                                    [123456789, 2.235461e+01, float('NaN'), float('NaN'), 1.715846e+01, 1.451727e+01,
                                     4.838556e-32, -9.957407e-33, -4.524045e-31, 4.901128e-30, 5.608559e-29,
                                     8.698059e-32, 2.798101e-33, 1.464481e-31, 5.201447e-32, 1.301941e-31],
                                    [428798990699423104, float('NaN'), 1.948665e+01, 1.782151e+01, 1.701492e+01,
                                     1.653498e+01, -6.904391e-32, 5.766324e-31, 2.691271e-30, 5.593872e-30,
                                     8.745204e-30, 3.407144e-32, 1.020666e-32, 1.911510e-32, 1.829784e-32,
                                     3.118226e-32],
                                    [5882658689230693632, float('NaN'), float('NaN'), 2.164732e+01, 1.801127e+01,
                                     1.493796e+01, -1.065495e-32, -4.320473e-33, 7.936535e-32, 2.234461e-30,
                                     3.806927e-29, 5.685276e-33, 7.746770e-34, 2.471102e-32, 1.745934e-32,
                                     6.280337e-32]])
def test_colour(sdss_std_cols, values):
    _phot_system = PhotometricSystem.SDSS_Std
    _label = _phot_system.get_system_label()
    data = pd.DataFrame(np.array([values]), columns=sdss_std_cols)
    corrected_data = apply_colour_equation(data, photometric_system=_phot_system, save_file=False)
    columns_that_change = [f'{_label}_mag_u', f'{_label}_flux_u', f'{_label}_flux_error_u']
    # Data that should remain unchanged
    static_data = data.drop(columns=columns_that_change)
    static_data = cast_output(static_data)
    static_corrected_data = corrected_data.drop(columns=columns_that_change)
    pdt.assert_frame_equal(static_corrected_data, static_data, rtol=1e-24, atol=1e-24)
    # Data that should have changed
    for column in columns_that_change:
        assert math.isnan(corrected_data[column].iloc[0])


def test_gaiaxpy_vs_pmn_photometry():
    """
    Compare the photometries got for a subset of sources of a particular CSV file for GaiaXPy and PMN's Java code.
    A subset of sources is used as it is not possible to extract the original data for all the sources in
    'Landolt_Johnson_STD_v375wiv142r_SAMPLE.csv' (PMN's photometry) from the archive. This test compares magnitude
    errors.
    """

    def __prepare_solution():
        # Sources for which data could be extracted from Geapre
        sources_to_keep = [4408087461749558912, 4408087908426160384, 4408088011505376128]
        # File corresponds to solution post-correction
        _jkc_solution = pd.read_csv(col_eq_sol_johnson_path)
        _jkc_solution.drop(columns=['BP-RP'], inplace=True)
        _jkc_solution = _jkc_solution.loc[_jkc_solution['source_id'].isin(sources_to_keep)].reset_index(drop=True)
        _jkc_solution = _cast(_jkc_solution)
        return _jkc_solution

    def __arrange_output(_output_photometry, _label):
        for column in _output_photometry.columns:
            if 'flux_error' in column:
                flux_col = f'{_label}_flux_{column[-1]}'
                flux_error_col = column.replace('flux', 'mag')
                _output_photometry[flux_error_col] = get_mag_error(_output_photometry[flux_col],
                                                                   _output_photometry[column])
        _output_photometry.drop(columns=[c for c in _output_photometry.columns if 'flux' in c], inplace=True)
        return _output_photometry

    phot_system = PhotometricSystem.JKC_Std
    label = phot_system.get_system_label()
    output_photometry = generate(colour_eq_csv_file, phot_system, save_file=False)
    output_photometry = __arrange_output(output_photometry, label)
    johnson_solution_df = __prepare_solution()
    pdt.assert_frame_equal(output_photometry, johnson_solution_df, check_like=True)
