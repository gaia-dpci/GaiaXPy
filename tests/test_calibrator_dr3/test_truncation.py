import numpy.testing as npt
import pytest

from gaiaxpy import calibrate
from gaiaxpy.core.generic_variables import RELEASES
from tests.files.continuous import (dr3_mean_spectra_fits_file, dr3_mean_spectra_csv_file,
                                    dr3_mean_spectra_xml_binary_file, dr3_mean_spectra_xml_plain_file,
                                    dr3_mean_spectra_avro_file, dr3_mean_spectra_ecsv_file)
from tests.reference.calibrator import sol_default_sampling_array, truncation_default_solution_df
from tests.utils.utils import assert_dfs_equal

_rtol, _atol = 1e-22, 1e-22


@pytest.mark.parametrize('file', [dr3_mean_spectra_avro_file, dr3_mean_spectra_csv_file, dr3_mean_spectra_ecsv_file,
                                  dr3_mean_spectra_fits_file, dr3_mean_spectra_xml_binary_file,
                                  dr3_mean_spectra_xml_plain_file])
def test_calibrate_both_bands_default_calibration_model_csv(file):
    # Default sampling and default calibration sampling
    spectra_df, positions = calibrate(file, truncation=True, save_file=False, release=RELEASES.dr3)
    npt.assert_array_equal(positions, sol_default_sampling_array)
    assert_dfs_equal(spectra_df, truncation_default_solution_df, rtol=_rtol, atol=_atol)
