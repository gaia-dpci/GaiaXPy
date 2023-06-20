import unittest

import numpy as np
import numpy.testing as npt
from pandas import testing as pdt

from gaiaxpy import calibrate
from gaiaxpy.calibrator.calibrator import _calibrate, _create_spectrum
from gaiaxpy.core.config import load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from tests.files.paths import mean_spectrum_csv_file, mean_spectrum_avro_file, mean_spectrum_fits_file, \
    mean_spectrum_xml_file, mean_spectrum_xml_plain_file
from tests.test_calibrator.calibrator_paths import solution_default_df, \
    solution_custom_df, solution_v211w_default_df, \
    solution_v211w_custom_df, sol_custom_sampling_array, sol_v211w_default_sampling_array, \
    sol_v211w_custom_sampling_array, sol_default_sampling_array

parser = InternalContinuousParser()

# Load variables
label = 'calibrator'
bp_model = 'v211w'  # Alternative bp model
xp_sampling_grid, xp_merge = load_xpmerge_from_xml(bp_model=bp_model)
xp_design_matrices = load_xpsampling_from_xml(bp_model=bp_model)

_rtol = 1e-10
_atol = 1e-10


def generate_single_spectrum(mean_spectrum_path):
    # Read mean Spectrum
    parsed_spectrum_file, extension = parser._parse(mean_spectrum_path)
    # Create sampled basis functions
    sampled_basis_func = {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid,
                                                                         xp_design_matrices[band]) for band in BANDS}
    first_row = parsed_spectrum_file.iloc[0]
    return _create_spectrum(first_row, truncation=False, design_matrix=sampled_basis_func, merge=xp_merge)


class TestCalibratorCSV(unittest.TestCase):

    def test_create_spectrum(self):
        spectrum = generate_single_spectrum(mean_spectrum_csv_file)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        spectra_df_csv, positions = calibrate(mean_spectrum_csv_file, save_file=False)
        npt.assert_array_equal(positions, sol_default_sampling_array)
        pdt.assert_frame_equal(spectra_df_csv, solution_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_csv_file, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, sol_custom_sampling_array)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, atol=_atol, rtol=_rtol)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_csv, positions = _calibrate(mean_spectrum_csv_file, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, sol_v211w_default_sampling_array)
        pdt.assert_frame_equal(spectra_df_csv, solution_v211w_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_csv_file, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, sol_custom_sampling_array)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, atol=_atol, rtol=_rtol)


class TestCalibratorAVRO(unittest.TestCase):

    def test_create_spectrum(self):
        spectrum = generate_single_spectrum(mean_spectrum_avro_file)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        spectra_df_avro, positions = calibrate(mean_spectrum_avro_file, save_file=False)
        npt.assert_array_equal(positions, sol_default_sampling_array)
        pdt.assert_frame_equal(spectra_df_avro, solution_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_avro_file, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, sol_custom_sampling_array)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, atol=_atol, rtol=_rtol)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_avro, positions = _calibrate(mean_spectrum_avro_file, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, sol_v211w_default_sampling_array)
        pdt.assert_frame_equal(spectra_df_avro, solution_v211w_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_avro_file, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, sol_v211w_custom_sampling_array)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, atol=_atol, rtol=_rtol)


class TestCalibratorFITS(unittest.TestCase):

    def test_create_spectrum(self):
        spectrum = generate_single_spectrum(mean_spectrum_fits_file)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        _spectra_df_fits, positions = calibrate(mean_spectrum_fits_file, save_file=False)
        npt.assert_array_equal(positions, sol_default_sampling_array)
        pdt.assert_frame_equal(_spectra_df_fits, solution_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_fits_file, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, sol_custom_sampling_array)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, atol=_atol, rtol=_rtol)

    def test_calibrate_both_bands_v211w_model(self):
        _spectra_df_fits, positions = _calibrate(mean_spectrum_fits_file, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, sol_v211w_default_sampling_array)
        pdt.assert_frame_equal(_spectra_df_fits, solution_v211w_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_fits_file, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, sol_v211w_custom_sampling_array)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, atol=_atol, rtol=_rtol)


class TestCalibratorXMLPlain(unittest.TestCase):

    def test_create_spectrum(self):
        spectrum = generate_single_spectrum(mean_spectrum_xml_plain_file)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        _spectra_df_xml_plain, positions = calibrate(mean_spectrum_xml_plain_file, save_file=False)
        npt.assert_array_equal(positions, sol_default_sampling_array)
        pdt.assert_frame_equal(_spectra_df_xml_plain, solution_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_xml_plain_file,
                                                          sampling=np.arange(350, 1050, 200), save_file=False)
        npt.assert_array_equal(positions, sol_custom_sampling_array)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, atol=_atol, rtol=_rtol)

    def test_calibrate_both_bands_v211w_model(self):
        _spectra_df_xml_plain, positions = _calibrate(mean_spectrum_xml_plain_file, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, sol_v211w_default_sampling_array)
        pdt.assert_frame_equal(_spectra_df_xml_plain, solution_v211w_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_xml_plain_file,
                                                           sampling=np.arange(350, 1050, 200), save_file=False,
                                                           bp_model=bp_model)
        npt.assert_array_equal(positions, sol_custom_sampling_array)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, atol=_atol, rtol=_rtol)


class TestCalibratorXML(unittest.TestCase):

    def test_create_spectrum(self):
        spectrum = generate_single_spectrum(mean_spectrum_xml_file)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        _spectra_df_xml, positions = calibrate(mean_spectrum_xml_file, save_file=False)
        npt.assert_array_equal(positions, sol_default_sampling_array)
        pdt.assert_frame_equal(_spectra_df_xml, solution_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_xml_file, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, sol_custom_sampling_array)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, atol=_atol, rtol=_rtol)

    def test_calibrate_both_bands_v211w_model(self):
        _spectra_df_xml, positions = _calibrate(mean_spectrum_xml_file, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, sol_v211w_default_sampling_array)
        pdt.assert_frame_equal(_spectra_df_xml, solution_v211w_default_df, atol=_atol, rtol=_rtol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_xml_file, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, sol_v211w_custom_sampling_array)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df)


class TestCalibratorSamplingRange(unittest.TestCase):

    def test_sampling_wrong_array(self):
        with self.assertRaises(ValueError):
            calibrate(mean_spectrum_avro_file, sampling=np.linspace(800, 350, 600), save_file=False)

    def test_sampling_low(self):
        with self.assertRaises(ValueError):
            calibrate(mean_spectrum_avro_file, sampling=np.linspace(300, 850, 300), save_file=False)

    def test_sampling_high(self):
        with self.assertRaises(ValueError):
            calibrate(mean_spectrum_avro_file, sampling=np.linspace(350, 1500, 200), save_file=False)

    def test_sampling_both_wrong(self):
        with self.assertRaises(ValueError):
            calibrate(mean_spectrum_avro_file, sampling=np.linspace(200, 2000, 100), save_file=False)
