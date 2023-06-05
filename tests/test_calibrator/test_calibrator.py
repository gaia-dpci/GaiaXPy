import unittest
from os.path import join

import numpy as np
import numpy.testing as npt
import pandas as pd
from pandas import testing as pdt

from gaiaxpy import calibrate
from gaiaxpy.calibrator.calibrator import _calibrate, _create_spectrum
from gaiaxpy.core.config import load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.utils import get_covariance_matrix
from tests.files.paths import files_path
from tests.utils.utils import df_columns_to_array, pos_file_to_array

parser = InternalContinuousParser()

# Load variables
label = 'calibrator'
bp_model = 'v211w'  # Alternative bp model
xp_sampling_grid, xp_merge = load_xpmerge_from_xml(bp_model=bp_model)
xp_design_matrices = load_xpsampling_from_xml(bp_model=bp_model)

# Path to solution files
calibrator_sol_path = join(files_path, 'calibrator_solution')

# Load XP continuous file
continuous_path = join(files_path, 'xp_continuous')
mean_spectrum_avro = join(continuous_path, 'MeanSpectrumSolutionWithCov.avro')
mean_spectrum_csv = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')
mean_spectrum_fits = join(continuous_path, 'XP_CONTINUOUS_RAW.fits')
mean_spectrum_xml = join(continuous_path, 'XP_CONTINUOUS_RAW.xml')
mean_spectrum_xml_plain = join(continuous_path, 'XP_CONTINUOUS_RAW_plain.xml')

# Load solution files, default model
solution_default_sampling = pos_file_to_array(join(calibrator_sol_path, 'calibrator_solution_default_sampling.csv'))
solution_custom_sampling = pos_file_to_array(join(calibrator_sol_path, 'calibrator_solution_custom_sampling.csv'))
solution_default_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_default.csv'), float_precision='high')
solution_custom_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_custom.csv'), float_precision='high')

# Load solution files, v211w model
solution_v211w_default_sampling = pos_file_to_array(join(calibrator_sol_path,
                                                         'calibrator_solution_v211w_default_sampling.csv'))
solution_v211w_custom_sampling = pos_file_to_array(join(calibrator_sol_path,
                                                        'calibrator_solution_v211w_custom_sampling.csv'))
solution_v211w_default_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_v211w_default.csv'),
                                        float_precision='high')
solution_v211w_custom_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_v211w_custom.csv'),
                                       float_precision='high')

# Parse arrays in solution_df
columns_to_parse = ['flux', 'flux_error']
solution_default_df = df_columns_to_array(solution_default_df, columns_to_parse)
solution_custom_df = df_columns_to_array(solution_custom_df, columns_to_parse)
solution_v211w_default_df = df_columns_to_array(solution_v211w_default_df, columns_to_parse)
solution_v211w_custom_df = df_columns_to_array(solution_v211w_custom_df, columns_to_parse)

_rtol = 1e-10
_atol = 1e-10


def generate_single_spectrum(mean_spectrum_path):
    # Read mean Spectrum
    parsed_spectrum_file, extension = parser.parse(mean_spectrum_path)
    for band in BANDS:
        parsed_spectrum_file[f'{band}_covariance_matrix'] = parsed_spectrum_file.apply(get_covariance_matrix,
                                                                                       axis=1, args=(band,))
    # Create sampled basis functions
    sampled_basis_func = {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid,
                                                                         xp_design_matrices[band]) for band in
                          BANDS}
    first_row = parsed_spectrum_file.iloc[0]
    return _create_spectrum(first_row, False, sampled_basis_func, xp_merge)


class TestCalibratorCSV(unittest.TestCase):

    def test_create_spectrum(self):
        spectrum = generate_single_spectrum(mean_spectrum_csv)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        spectra_df_csv, positions = calibrate(mean_spectrum_csv, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(spectra_df_csv, solution_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_csv, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, atol=_atol, rtol=_rtol)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_csv, positions = _calibrate(mean_spectrum_csv, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(spectra_df_csv, solution_v211w_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_csv, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, atol=_atol, rtol=_rtol)


class TestCalibratorAVRO(unittest.TestCase):

    def test_create_spectrum(self):
        spectrum = generate_single_spectrum(mean_spectrum_avro)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        spectra_df_avro, positions = calibrate(mean_spectrum_avro, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(spectra_df_avro, solution_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_avro, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, atol=_atol, rtol=_rtol)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_avro, positions = _calibrate(mean_spectrum_avro, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(spectra_df_avro, solution_v211w_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_avro, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, atol=_atol, rtol=_rtol)


class TestCalibratorFITS(unittest.TestCase):

    def test_create_spectrum(self):
        spectrum = generate_single_spectrum(mean_spectrum_fits)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        _spectra_df_fits, positions = calibrate(mean_spectrum_fits, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(_spectra_df_fits, solution_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_fits, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, atol=_atol, rtol=_rtol)

    def test_calibrate_both_bands_v211w_model(self):
        _spectra_df_fits, positions = _calibrate(mean_spectrum_fits, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(_spectra_df_fits, solution_v211w_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_fits, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, atol=_atol, rtol=_rtol)


class TestCalibratorXMLPlain(unittest.TestCase):

    def test_create_spectrum(self):
        spectrum = generate_single_spectrum(mean_spectrum_xml_plain)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        _spectra_df_xml_plain, positions = calibrate(mean_spectrum_xml_plain, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(_spectra_df_xml_plain, solution_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_xml_plain, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, atol=_atol, rtol=_rtol)

    def test_calibrate_both_bands_v211w_model(self):
        _spectra_df_xml_plain, positions = _calibrate(mean_spectrum_xml_plain, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(_spectra_df_xml_plain, solution_v211w_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_xml_plain, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, atol=_atol, rtol=_rtol)


class TestCalibratorXML(unittest.TestCase):

    def test_create_spectrum(self):
        spectrum = generate_single_spectrum(mean_spectrum_xml)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        _spectra_df_xml, positions = calibrate(mean_spectrum_xml, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(_spectra_df_xml, solution_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_xml, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, atol=_atol, rtol=_rtol)

    def test_calibrate_both_bands_v211w_model(self):
        _spectra_df_xml, positions = _calibrate(mean_spectrum_xml, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(_spectra_df_xml, solution_v211w_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_xml, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df)


class TestCalibratorSamplingRange(unittest.TestCase):

    def test_sampling_wrong_array(self):
        with self.assertRaises(ValueError):
            calibrate(mean_spectrum_avro, sampling=np.linspace(800, 350, 600), save_file=False)

    def test_sampling_low(self):
        with self.assertRaises(ValueError):
            calibrate(mean_spectrum_avro, sampling=np.linspace(300, 850, 300), save_file=False)

    def test_sampling_high(self):
        with self.assertRaises(ValueError):
            calibrate(mean_spectrum_avro, sampling=np.linspace(350, 1500, 200), save_file=False)

    def test_sampling_both_wrong(self):
        with self.assertRaises(ValueError):
            calibrate(mean_spectrum_avro, sampling=np.linspace(200, 2000, 100), save_file=False)


class TestCalibratorSingleElement(unittest.TestCase):

    def test_single_element_query(self):
        query = "SELECT * FROM gaiadr3.gaia_source WHERE source_id='5853498713190525696'"
        output_df, sampling = calibrate(query, save_file=False)
        source_data_output = output_df[output_df['source_id'] == 5853498713190525696]
        source_data_solution = solution_default_df[solution_default_df['source_id'] == 5853498713190525696]
        pdt.assert_frame_equal(source_data_output, source_data_solution, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, solution_default_sampling)
