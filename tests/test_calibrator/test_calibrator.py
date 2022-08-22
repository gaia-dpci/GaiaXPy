import unittest
import numpy as np
import pandas as pd
import numpy.testing as npt
from pandas import testing as pdt
from numpy import ndarray
from gaiaxpy.calibrator.calibrator import _calibrate, _create_spectrum
from gaiaxpy.core import satellite
from gaiaxpy.core.config import _load_xpmerge_from_csv, _load_xpsampling_from_csv
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from os.path import join
from tests.files import files_path
from tests.utils import df_columns_to_array, pos_file_to_array
from gaiaxpy import calibrate


parser = InternalContinuousParser()

# Load variables
label = 'calibrator'
bp_model = 'v211w'  # Alternative bp model
xp_sampling_grid, xp_merge = _load_xpmerge_from_csv(label, bp_model=bp_model)
xp_design_matrices = _load_xpsampling_from_csv(label, bp_model=bp_model)

# Path to solution files
calibrator_sol_path = join(files_path, 'calibrator_solution')

# Load XP continuous file
continuous_path = join(files_path, 'xp_continuous')
mean_spectrum_avro = join(continuous_path, 'MeanSpectrumSolutionWithCov.avro')
mean_spectrum_csv = join(continuous_path, 'XP_CONTINUOUS_RAW.csv')
mean_spectrum_fits = join(continuous_path, 'XP_CONTINUOUS_RAW.fits')
mean_spectrum_xml = join(continuous_path, 'XP_CONTINUOUS_RAW.xml')
mean_spectrum_xml_plain = join(continuous_path, 'XP_CONTINUOUS_RAW_plain.xml')

# Calibrate data in files
spectra_df_fits = _calibrate(mean_spectrum_fits, save_file=False, bp_model=bp_model)
spectra_df_xml = _calibrate(mean_spectrum_xml, save_file=False, bp_model=bp_model)
spectra_df_xml_plain = _calibrate(mean_spectrum_xml_plain, save_file=False, bp_model=bp_model)

# Load solution files, default model
solution_default_sampling = pos_file_to_array(join(calibrator_sol_path, 'calibrator_solution_default_sampling.csv'))
solution_custom_sampling = pos_file_to_array(join(calibrator_sol_path, 'calibrator_solution_custom_sampling.csv'))
solution_default_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_default.csv'), float_precision='round_trip')
solution_custom_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_custom.csv'), float_precision='round_trip')

# Load solution files, v211w model
solution_v211w_default_sampling = pos_file_to_array(join(calibrator_sol_path,
                                                         'calibrator_solution_v211w_default_sampling.csv'))
solution_v211w_custom_sampling = pos_file_to_array(join(calibrator_sol_path, 'calibrator_solution_v211w_custom_sampling.csv'))
solution_v211w_default_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_v211w_default.csv'),
                                        float_precision='round_trip')
solution_v211w_custom_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_v211w_custom.csv'),
                                       float_precision='round_trip')

# Parse arrays in solution_df
columns_to_parse = ['flux', 'flux_error']
solution_default_df = df_columns_to_array(solution_default_df, columns_to_parse)
solution_custom_df = df_columns_to_array(solution_custom_df, columns_to_parse)
solution_v211w_default_df = df_columns_to_array(solution_v211w_default_df, columns_to_parse)
solution_v211w_custom_df = df_columns_to_array(solution_v211w_custom_df, columns_to_parse)


class TestCalibratorCSV(unittest.TestCase):

    def test_create_spectrum(self):
        # Read mean Spectrum
        parsed_spectrum_file, extension = parser.parse(mean_spectrum_csv)
        # Create sampled basis functions
        sampled_basis_func = {}
        for band in satellite.BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(
                xp_sampling_grid, xp_design_matrices[band])
        first_row = parsed_spectrum_file.iloc[0]
        spectrum = _create_spectrum(first_row, False, sampled_basis_func, xp_merge)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        spectra_df_csv, positions = calibrate(mean_spectrum_csv, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(spectra_df_csv, solution_default_df)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(
            mean_spectrum_csv,
            sampling=np.arange(350, 1050, 200),
            save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_csv, positions = _calibrate(mean_spectrum_csv, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(spectra_df_csv, solution_v211w_default_df)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(
            mean_spectrum_csv,
            sampling=np.arange(350, 1050, 200),
            save_file=False,
            bp_model=bp_model)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df)


class TestCalibratorAVRO(unittest.TestCase):

    def test_create_spectrum(self):
        # Read mean Spectrum
        parsed_spectrum_file, extension = parser.parse(mean_spectrum_avro)
        # Create sampled basis functions
        sampled_basis_func = {}
        for band in satellite.BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(
                xp_sampling_grid, xp_design_matrices[band])
        first_row = parsed_spectrum_file.iloc[0]
        spectrum = _create_spectrum(first_row, False, sampled_basis_func, xp_merge)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        spectra_df_avro, positions = calibrate(mean_spectrum_avro, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(spectra_df_avro, solution_default_df)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(
            mean_spectrum_avro,
            sampling=np.arange(350, 1050, 200),
            save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_avro, positions = _calibrate(mean_spectrum_avro, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(spectra_df_avro, solution_v211w_default_df)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(
            mean_spectrum_avro,
            sampling=np.arange(350, 1050, 200),
            save_file=False,
            bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df)


class TestCalibratorFITS(unittest.TestCase):

    def test_create_spectrum(self):
        # Read mean Spectrum
        parsed_spectrum_file, extension = parser.parse(mean_spectrum_fits)
        # Create sampled basis functions
        sampled_basis_func = {}
        for band in satellite.BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(
                xp_sampling_grid, xp_design_matrices[band])
        first_row = parsed_spectrum_file.iloc[0]
        spectrum = _create_spectrum(first_row, False, sampled_basis_func, xp_merge)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        spectra_df_fits, positions = calibrate(mean_spectrum_fits, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(spectra_df_fits, solution_default_df)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(
            mean_spectrum_fits,
            sampling=np.arange(350, 1050, 200),
            save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_fits, positions = _calibrate(mean_spectrum_fits, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(spectra_df_fits, solution_v211w_default_df)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(
            mean_spectrum_fits,
            sampling=np.arange(350, 1050, 200),
            save_file=False,
            bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df)


class TestCalibratorXMLPlain(unittest.TestCase):

    def test_create_spectrum(self):
        # Read mean Spectrum
        parsed_spectrum_file, extension = parser.parse(mean_spectrum_xml_plain)
        # Create sampled basis functions
        sampled_basis_func = {}
        for band in satellite.BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(
                xp_sampling_grid, xp_design_matrices[band])
        first_row = parsed_spectrum_file.iloc[0]
        spectrum = _create_spectrum(first_row, False, sampled_basis_func, xp_merge)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        spectra_df_xml_plain, positions = calibrate(mean_spectrum_xml_plain, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(spectra_df_xml_plain, solution_default_df)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(
            mean_spectrum_xml_plain,
            sampling=np.arange(350, 1050, 200),
            save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_xml_plain, positions = _calibrate(mean_spectrum_xml_plain, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(spectra_df_xml_plain, solution_v211w_default_df)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(
            mean_spectrum_xml_plain,
            sampling=np.arange(350, 1050, 200),
            save_file=False,
            bp_model=bp_model)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df)


class TestCalibratorXML(unittest.TestCase):

    def test_create_spectrum(self):
        # Read mean Spectrum
        parsed_spectrum_file, extension = parser.parse(mean_spectrum_xml)
        # Create sampled basis functions
        sampled_basis_func = {}
        for band in satellite.BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(
                xp_sampling_grid, xp_design_matrices[band])
        first_row = parsed_spectrum_file.iloc[0]
        spectrum = _create_spectrum(first_row, False, sampled_basis_func, xp_merge)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        spectra_df_xml, positions = calibrate(mean_spectrum_xml, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(spectra_df_xml, solution_default_df)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(
            mean_spectrum_xml,
            sampling=np.arange(350, 1050, 200),
            save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_xml, positions = _calibrate(mean_spectrum_xml, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(spectra_df_xml, solution_v211w_default_df)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(
            mean_spectrum_xml,
            sampling=np.arange(350, 1050, 200),
            save_file=False,
            bp_model=bp_model)
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
        pdt.assert_frame_equal(source_data_output, source_data_solution)
        npt.assert_array_equal(sampling, solution_default_sampling)
