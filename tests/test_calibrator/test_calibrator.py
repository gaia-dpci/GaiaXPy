import numpy as np
import numpy.testing as npt
import pytest
from pandas import testing as pdt

from gaiaxpy import calibrate
from gaiaxpy.calibrator.calibrator import _calibrate, _create_spectrum
from gaiaxpy.core.config import load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from tests.files.paths import (mean_spectrum_csv_file, mean_spectrum_avro_file, mean_spectrum_fits_file,
                               mean_spectrum_xml_file, mean_spectrum_xml_plain_file, mean_spectrum_ecsv_file)
from tests.test_calibrator.calibrator_solutions import (solution_default_df, solution_custom_df,
                                                        solution_v211w_default_df, solution_v211w_custom_df,
                                                        sol_custom_sampling_array, sol_v211w_default_sampling_array,
                                                        sol_default_sampling_array)
from tests.utils.utils import is_instance_err_message, npt_array_err_message

# Load variables
bp_model = 'v211w'  # Alternative bp model

_atol, _rtol = 1e-10, 1e-10

cal_input_files = [mean_spectrum_avro_file, mean_spectrum_csv_file, mean_spectrum_ecsv_file, mean_spectrum_fits_file,
                   mean_spectrum_xml_file, mean_spectrum_xml_plain_file]


@pytest.mark.parametrize('input_file', cal_input_files)
def test_create_spectrum(input_file):
    def generate_single_spectrum(mean_spectrum_path):
        xp_design_matrices = load_xpsampling_from_xml(bp_model=bp_model)
        xp_sampling_grid, xp_merge = load_xpmerge_from_xml(bp_model=bp_model)
        # Read mean Spectrum
        parser = InternalContinuousParser(MANDATORY_INPUT_COLS['calibrate'] + CORR_INPUT_COLUMNS)
        parsed_spectrum_file, extension = parser.parse_file(mean_spectrum_path)
        # Create sampled basis functions
        sampled_basis_func = {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_design_matrices[band])
                              for band in BANDS}
        return _create_spectrum(parsed_spectrum_file.iloc[0], truncation=False, design_matrix=sampled_basis_func,
                                merge=xp_merge)

    spectrum = generate_single_spectrum(input_file)
    assert isinstance(spectrum, AbsoluteSampledSpectrum), is_instance_err_message(input_file, AbsoluteSampledSpectrum)


@pytest.mark.parametrize('input_file', cal_input_files)
def test_calibrate_both_bands_default_calibration_model(input_file, request):
    # Default sampling and default calibration sampling
    spectra_df_csv, positions = calibrate(input_file, save_file=False)
    npt.assert_array_equal(positions, sol_default_sampling_array, err_msg=npt_array_err_message(input_file))
    try:
        pdt.assert_frame_equal(spectra_df_csv, solution_default_df, atol=_atol, rtol=_rtol)
    except AssertionError as e:
        print(f'{request.node.name} failed for file: {input_file}.')
        raise e


@pytest.mark.parametrize('input_file', cal_input_files)
def test_custom_sampling_default_calibration_model(input_file):
    spectra_df_custom_sampling, positions = calibrate(input_file, sampling=np.arange(350, 1050, 200), save_file=False)
    npt.assert_array_equal(positions, sol_custom_sampling_array, err_msg=npt_array_err_message(input_file))
    pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, atol=_atol, rtol=_rtol)


@pytest.mark.parametrize('sampling,sampling_sol,solution', [(None, sol_v211w_default_sampling_array,
                                                             solution_v211w_default_df),
                                                            (np.arange(350, 1050, 200), sol_custom_sampling_array,
                                                             solution_v211w_custom_df)])
@pytest.mark.parametrize('input_file', cal_input_files)
def test_custom_sampling_v211w_model(input_file, sampling, sampling_sol, solution):
    spectra_df_custom_sampling, positions = _calibrate(input_file, sampling=sampling, save_file=False,
                                                       bp_model=bp_model)
    npt.assert_array_equal(positions, sampling_sol, err_msg=npt_array_err_message(input_file))
    pdt.assert_frame_equal(spectra_df_custom_sampling, solution, atol=_atol, rtol=_rtol)


@pytest.mark.parametrize('array', [np.linspace(800, 350, 600), np.linspace(300, 850, 300),
                                   np.linspace(350, 1500, 200), np.linspace(200, 2000, 100)])
def test_sampling_wrong_array(array):
    with pytest.raises(ValueError):
        calibrate(mean_spectrum_avro_file, sampling=array, save_file=False)
