import unittest
from os.path import join

import numpy as np
import numpy.testing as npt
import pandas as pd
from pandas import testing as pdt

from gaiaxpy import calibrate
from gaiaxpy.calibrator.calibrator import _calibrate, _create_spectrum
from gaiaxpy.core import satellite
from gaiaxpy.core.config import _load_xpmerge_from_xml, _load_xpsampling_from_xml
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from tests.files.paths import files_path
from tests.utils.utils import pos_file_to_array

parser = InternalContinuousParser()

# Load variables
label = 'calibrator'
bp_model = 'v211w'  # Alternative bp model
xp_sampling_grid, xp_merge = _load_xpmerge_from_xml(bp_model=bp_model)
xp_design_matrices = _load_xpsampling_from_xml(bp_model=bp_model)

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

# Generate converters
columns_to_parse = ['flux', 'flux_error']
converters = dict([(column, lambda x: str_to_array(x)) for column in columns_to_parse])

# Load solution files, default model
solution_default_sampling = pos_file_to_array(join(calibrator_sol_path, 'calibrator_solution_default_sampling.csv'))
solution_custom_sampling = pos_file_to_array(join(calibrator_sol_path, 'calibrator_solution_custom_sampling.csv'))
solution_default_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_default.csv'),
                                  float_precision='round_trip', converters=converters)
solution_custom_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_custom.csv'),
                                 float_precision='round_trip', converters=converters)

# Load solution files, v211w model
solution_v211w_default_sampling = pos_file_to_array(join(calibrator_sol_path,
                                                         'calibrator_solution_v211w_default_sampling.csv'))
solution_v211w_custom_sampling = pos_file_to_array(join(calibrator_sol_path,
                                                        'calibrator_solution_v211w_custom_sampling.csv'))
solution_v211w_default_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_v211w_default.csv'),
                                        float_precision='round_trip', converters=converters)
solution_v211w_custom_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_v211w_custom.csv'),
                                       float_precision='round_trip', converters=converters)

_rtol, _atol = 1e-23, 1e-23


class TestCalibratorCSV(unittest.TestCase):

    def test_create_spectrum(self):
        # Read mean Spectrum
        parsed_spectrum_file, extension = parser.parse(mean_spectrum_csv)
        # Create sampled basis functions
        sampled_basis_func = {}
        for band in satellite.BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(xp_sampling_grid,
                                                                                xp_design_matrices[band])
        first_row = parsed_spectrum_file.iloc[0]
        spectrum = _create_spectrum(first_row, False, sampled_basis_func, xp_merge)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        spectra_df_csv, positions = calibrate(mean_spectrum_csv, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(spectra_df_csv, solution_default_df, rtol=_rtol, atol=_atol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_csv, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, rtol=_rtol, atol=_atol)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_csv, positions = _calibrate(mean_spectrum_csv, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(spectra_df_csv, solution_v211w_default_df, rtol=_rtol, atol=_atol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_csv, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, rtol=_rtol, atol=_atol)


class TestCalibratorAVRO(unittest.TestCase):

    def test_create_spectrum(self):
        # Read mean Spectrum
        parsed_spectrum_file, extension = parser.parse(mean_spectrum_avro)
        # Create sampled basis functions
        sampled_basis_func = {}
        for band in satellite.BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(xp_sampling_grid,
                                                                                xp_design_matrices[band])
        first_row = parsed_spectrum_file.iloc[0]
        spectrum = _create_spectrum(first_row, False, sampled_basis_func, xp_merge)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        spectra_df_avro, positions = calibrate(mean_spectrum_avro, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(spectra_df_avro, solution_default_df, rtol=_rtol, atol=_atol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_avro, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, rtol=_rtol, atol=_atol)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_avro, positions = _calibrate(mean_spectrum_avro, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(spectra_df_avro, solution_v211w_default_df, rtol=_rtol, atol=_atol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_avro, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, rtol=_rtol, atol=_atol)


class TestCalibratorFITS(unittest.TestCase):

    def test_create_spectrum(self):
        # Read mean Spectrum
        parsed_spectrum_file, extension = parser.parse(mean_spectrum_fits)
        # Create sampled basis functions
        sampled_basis_func = {}
        for band in satellite.BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(xp_sampling_grid,
                                                                                xp_design_matrices[band])
        first_row = parsed_spectrum_file.iloc[0]
        spectrum = _create_spectrum(first_row, False, sampled_basis_func, xp_merge)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        _spectra_df_fits, positions = calibrate(mean_spectrum_fits, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(_spectra_df_fits, solution_default_df, rtol=_rtol, atol=_atol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_fits, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, rtol=_rtol, atol=_atol)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_fits, positions = _calibrate(mean_spectrum_fits, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(spectra_df_fits, solution_v211w_default_df, rtol=_rtol, atol=_atol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_fits, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, rtol=_rtol, atol=_atol)


class TestCalibratorXMLPlain(unittest.TestCase):

    def test_create_spectrum(self):
        # Read mean Spectrum
        parsed_spectrum_file, extension = parser.parse(mean_spectrum_xml_plain)
        # Create sampled basis functions
        sampled_basis_func = {}
        for band in satellite.BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(xp_sampling_grid,
                                                                                xp_design_matrices[band])
        first_row = parsed_spectrum_file.iloc[0]
        spectrum = _create_spectrum(first_row, False, sampled_basis_func, xp_merge)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        _spectra_df_xml_plain, positions = calibrate(mean_spectrum_xml_plain, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(_spectra_df_xml_plain, solution_default_df, rtol=_rtol, atol=_atol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_xml_plain, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, rtol=_rtol, atol=_atol)

    def test_calibrate_both_bands_v211w_model(self):
        _spectra_df_xml_plain, positions = _calibrate(mean_spectrum_xml_plain, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(_spectra_df_xml_plain, solution_v211w_default_df, rtol=_rtol, atol=_atol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_xml_plain, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, rtol=_rtol, atol=_atol)


class TestCalibratorXML(unittest.TestCase):

    def test_create_spectrum(self):
        # Read mean Spectrum
        parsed_spectrum_file, extension = parser.parse(mean_spectrum_xml)
        # Create sampled basis functions
        sampled_basis_func = {}
        for band in satellite.BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(xp_sampling_grid,
                                                                                xp_design_matrices[band])
        first_row = parsed_spectrum_file.iloc[0]
        spectrum = _create_spectrum(first_row, False, sampled_basis_func, xp_merge)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model(self):
        # Default sampling and default calibration sampling
        _spectra_df_xml, positions = calibrate(mean_spectrum_xml, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(_spectra_df_xml, solution_default_df, rtol=_rtol, atol=_atol)

    def test_custom_sampling_default_calibration_model(self):
        spectra_df_custom_sampling, positions = calibrate(mean_spectrum_xml, sampling=np.arange(350, 1050, 200),
                                                          save_file=False)
        npt.assert_array_equal(positions, solution_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_custom_df, rtol=_rtol, atol=_atol)

    def test_calibrate_both_bands_v211w_model(self):
        spectra_df_xml, positions = _calibrate(mean_spectrum_xml, save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_default_sampling)
        pdt.assert_frame_equal(spectra_df_xml, solution_v211w_default_df, rtol=_rtol, atol=_atol)

    def test_custom_sampling_v211w_model(self):
        spectra_df_custom_sampling, positions = _calibrate(mean_spectrum_xml, sampling=np.arange(350, 1050, 200),
                                                           save_file=False, bp_model=bp_model)
        npt.assert_array_equal(positions, solution_v211w_custom_sampling)
        pdt.assert_frame_equal(spectra_df_custom_sampling, solution_v211w_custom_df, rtol=_rtol, atol=_atol)


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
        source_id = 5853498713190525696
        query = f"SELECT * FROM gaiadr3.gaia_source WHERE source_id='{source_id}'"
        output_df, sampling = calibrate(query, save_file=False)
        source_data_output = output_df[output_df['source_id'] == 5853498713190525696]
        source_data_solution = solution_default_df[solution_default_df['source_id'] == source_id]
        pdt.assert_frame_equal(source_data_output, source_data_solution, rtol=_rtol, atol=_atol)
        npt.assert_array_equal(sampling, solution_default_sampling)
