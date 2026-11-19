import numpy as np
import numpy.testing as npt
import pytest

from gaiaxpy import calibrate
from gaiaxpy.core.generic_variables import RELEASES
from tests.files.continuous import (dr3_mean_spectra_csv_file, dr3_mean_spectra_avro_file, dr3_mean_spectra_fits_file,
                                    dr3_mean_spectra_xml_binary_file, dr3_mean_spectra_xml_plain_file,
                                    dr3_mean_spectra_ecsv_file)
from tests.reference.calibrator import (solution_default_df, solution_custom_df, sol_custom_sampling_array,
                                        sol_default_sampling_array)
from tests.utils.utils import npt_array_err_message, assert_dfs_equal

_atol, _rtol = 1e-12, 1e-12

cal_input_files = [dr3_mean_spectra_avro_file, dr3_mean_spectra_csv_file, dr3_mean_spectra_ecsv_file,
                   dr3_mean_spectra_fits_file,
                   dr3_mean_spectra_xml_binary_file, dr3_mean_spectra_xml_plain_file]


@pytest.mark.parametrize('input_file', cal_input_files)
def test_calibrate_both_bands_default_calibration_model(input_file):
    # Default sampling and default calibration sampling
    spectra_df_csv, positions = calibrate(input_file, save_file=False, release=RELEASES.dr3)
    npt.assert_array_equal(positions, sol_default_sampling_array, err_msg=npt_array_err_message(input_file))
    assert_dfs_equal(spectra_df_csv, solution_default_df, atol=1e-23, rtol=_rtol)


@pytest.mark.parametrize('input_file', cal_input_files)
def test_custom_sampling_default_calibration_model(input_file):
    spectra_df_custom_sampling, positions = calibrate(input_file, sampling=np.arange(350, 1050, 200), save_file=False,
                                                      release=RELEASES.dr3)
    npt.assert_array_equal(positions, sol_custom_sampling_array, err_msg=npt_array_err_message(input_file))
    assert_dfs_equal(spectra_df_custom_sampling, solution_custom_df, atol=1e-21, rtol=_rtol)


@pytest.mark.parametrize('array', [np.linspace(800, 350, 600), np.linspace(300, 850, 300),
                                   np.linspace(350, 1500, 200), np.linspace(200, 2000, 100)])
def test_sampling_wrong_array(array):
    with pytest.raises(ValueError):
        calibrate(dr3_mean_spectra_avro_file, sampling=array, save_file=False)
