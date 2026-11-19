import pandas as pd
import pytest

from gaiaxpy import generate, apply_error_correction, PhotometricSystem
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.file_parser.cast import _cast
from tests.files.continuous import dr3_mean_spectra_csv_file
from tests.files.error_correction import corrected_error_solution_path, phot_with_nan_corrected_sol_path
from tests.files.error_correction import phot_with_nan_path
from tests.utils.utils import assert_dfs_equal

_ertol, _eatol = 1e-24, 1e-24
_rtol, _atol = 1e-15, 1e-15


def compare_all_columns(corrected_multiphotometry, solution):
    error_columns = [column for column in corrected_multiphotometry.columns if 'error' in column]
    other_columns = [column for column in corrected_multiphotometry.columns if 'error' not in column]
    assert_dfs_equal(corrected_multiphotometry[error_columns], solution[error_columns], rtol=_ertol, atol=_eatol)
    assert_dfs_equal(corrected_multiphotometry[other_columns], solution[other_columns], rtol=_rtol, atol=_atol)


def test_error_correction_no_vega():
    phot_list = [PhotometricSystem.DR3_Euclid_VIS, PhotometricSystem.DR3_HST_HUGS_Std]
    multi_synthetic_photometry = generate(dr3_mean_spectra_csv_file, photometric_system=phot_list, save_file=False)
    with pytest.raises(ValueError):
        apply_error_correction(multi_synthetic_photometry, release=RELEASES.dr3, save_file=False)


def test_photometry_with_nan():
    phot_with_nan_df = pd.read_csv(phot_with_nan_path, **CSV_FLOAT_PRECISION_KWARGS)
    output = apply_error_correction(phot_with_nan_df, release=RELEASES.dr3, save_file=False)
    solution = pd.read_csv(phot_with_nan_corrected_sol_path, **CSV_FLOAT_PRECISION_KWARGS)
    assert_dfs_equal(output, _cast(solution), rtol=1e-15, atol=0)


def test_single_phot_object():
    phot_system = PhotometricSystem.DR3_Gaia_Vega
    synthetic_photometry = generate(dr3_mean_spectra_csv_file, photometric_system=phot_system, save_file=False)
    corrected_synth_phot = apply_error_correction(synthetic_photometry, release=RELEASES.dr3, save_file=False)
    corrected_errors_df = pd.read_csv(corrected_error_solution_path, usecols=corrected_synth_phot.columns,
                                      **CSV_FLOAT_PRECISION_KWARGS)
    corrected_errors_df = _cast(corrected_errors_df)
    compare_all_columns(corrected_errors_df, corrected_synth_phot)


def test_error_correction():
    phot_list = [PhotometricSystem.DR3_Euclid_VIS, PhotometricSystem.DR3_Gaia_Vega, PhotometricSystem.DR3_HST_HUGS_Std]
    multi_synthetic_photometry = generate(dr3_mean_spectra_csv_file, photometric_system=phot_list, save_file=False)
    corrected_multiphotometry = apply_error_correction(multi_synthetic_photometry, release=RELEASES.dr3,
                                                       save_file=False)
    # Load solution
    corrected_solution = pd.read_csv(corrected_error_solution_path, **CSV_FLOAT_PRECISION_KWARGS)
    corrected_solution = _cast(corrected_solution)
    compare_all_columns(corrected_multiphotometry, corrected_solution)


def test_error_correction_system_with_no_table():
    # Halpha system has got no correction table
    phot_list = [PhotometricSystem.DR3_Euclid_VIS, PhotometricSystem.DR3_Gaia_Vega,
                 PhotometricSystem.DR3_Halpha_Custom_AB]
    multi_photometry = generate(dr3_mean_spectra_csv_file, photometric_system=phot_list, save_file=False)
    # Extract Halpha columns from the original photometry
    halpha_columns = [column for column in multi_photometry.columns if column.startswith('DR3_HalphaCustomAb_')]
    corrected_multi_photometry = apply_error_correction(multi_photometry, release=RELEASES.dr3, save_file=False)
    halpha_photometry = multi_photometry[halpha_columns]  # The results for this system should not change
    # Load solution
    corrected_solution = pd.read_csv(corrected_error_solution_path, **CSV_FLOAT_PRECISION_KWARGS)
    corrected_solution = _cast(corrected_solution)
    hst_columns = [column for column in corrected_solution.columns if column.startswith('DR3_HstHugsStd_')]
    corrected_multiphotometry_solution_no_hst = corrected_solution.drop(columns=hst_columns)
    complete_solution = pd.concat([corrected_multiphotometry_solution_no_hst, halpha_photometry], axis=1)
    compare_all_columns(corrected_multi_photometry, complete_solution)
