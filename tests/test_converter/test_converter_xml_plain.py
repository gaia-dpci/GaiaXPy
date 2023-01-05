import unittest
from ast import literal_eval
from configparser import ConfigParser
from itertools import islice
from os.path import abspath, dirname, join

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import convert
from gaiaxpy.config.paths import config_path
from gaiaxpy.converter.config import load_config
from gaiaxpy.converter.converter import _create_spectrum, get_design_matrices, \
    get_unique_basis_ids
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.file_parser.parse_internal_sampled import InternalSampledParser
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.xp_sampled_spectrum import XpSampledSpectrum
from tests.files.paths import files_path
from tests.utils.utils import get_spectrum_with_source_id_and_xp

current_path = abspath(dirname(__file__))
configparser = ConfigParser()
configparser.read(join(config_path, 'config.ini'))
config_file = join(config_path, configparser.get('converter', 'optimised_bases'))
config_df = load_config(config_file)

# Generate converters
columns_to_parse = ['flux', 'flux_error']
converters = dict([(column, lambda x: str_to_array(x)) for column in columns_to_parse])

# File under test
continuous_path = join(files_path, 'xp_continuous')
input_file = join(continuous_path, 'XP_CONTINUOUS_RAW_plain.xml')
converter_solution_path = join(files_path, 'converter_solution')
converter_solution_df = pd.read_csv(join(converter_solution_path, 'converter_solution_0_60_481.csv'),
                                    float_precision='round_trip', converters=converters)
missing_band_solution = join(converter_solution_path, 'missing_band_default_sampling_solution.csv')

# Parsers
parser = InternalContinuousParser()
# Parsed files
parsed_input, _ = parser.parse(input_file)

sampling = np.linspace(0, 60, 481)
unique_bases_ids = get_unique_basis_ids(parsed_input)
design_matrices = get_design_matrices(unique_bases_ids, sampling, config_df)

converted_df, positions = convert(input_file, sampling=sampling, save_file=False)

# Files to compare the sampled spectrum with value by value without/with truncation applied
ref_sampled_csv = join(converter_solution_path, 'SampledMeanSpectrum.csv')
ref_sampled_truncated_csv = join(converter_solution_path, 'SampledMeanSpectrum_truncated.csv')

sampled_parser = InternalSampledParser()
ref_sampled, _ = sampled_parser.parse(ref_sampled_csv)
ref_sampled_truncated, _ = sampled_parser.parse(ref_sampled_truncated_csv)

TOL = 4
_rtol, _atol = 1e-11, 1e-11


class TestGetMethods(unittest.TestCase):

    def test_get_unique_basis_ids(self):
        self.assertIsInstance(unique_bases_ids, set)
        self.assertEqual(unique_bases_ids, {56, 57})

    def test_get_design_matrices(self):
        self.assertIsInstance(design_matrices, dict)
        self.assertEqual(len(design_matrices), 2)
        self.assertEqual(list(design_matrices.keys()), [56, 57])
        self.assertIsInstance(design_matrices[56], SampledBasisFunctions)
        self.assertIsInstance(design_matrices[57], SampledBasisFunctions)


class TestCreateSpectrum(unittest.TestCase):

    def test_create_spectrum(self):
        truncation = True
        for index, row in islice(
                parsed_input.iterrows(), 1):  # Just the first row
            spectrum_bp = _create_spectrum(
                row, truncation, design_matrices, BANDS.bp)
            spectrum_rp = _create_spectrum(
                row, truncation, design_matrices, BANDS.rp)
        self.assertIsInstance(spectrum_bp, XpSampledSpectrum)
        self.assertIsInstance(spectrum_rp, XpSampledSpectrum)
        self.assertEqual(spectrum_bp.get_source_id(), spectrum_rp.get_source_id())
        self.assertEqual(spectrum_bp.get_xp(), BANDS.bp)
        self.assertEqual(spectrum_rp.get_xp(), BANDS.rp)


class TestConverter(unittest.TestCase):

    def test_converter_both_types(self):
        self.assertIsInstance(converted_df, pd.DataFrame)
        self.assertEqual(len(converted_df), 4)
        pdt.assert_frame_equal(converted_df, converter_solution_df, rtol=_rtol, atol=_atol)

    def test_conversion(self):
        for index, spectrum in converted_df.iterrows():
            band = spectrum['xp']
            ref = get_spectrum_with_source_id_and_xp(spectrum.source_id, band, ref_sampled)
            npt.assert_almost_equal(ref['flux'], spectrum.flux, decimal=TOL)
            npt.assert_almost_equal(ref['error'], spectrum.flux_error, decimal=TOL)


class TestTruncation(unittest.TestCase):

    def test_truncation(self):
        converted_truncated_df, _ = convert(input_file, sampling=sampling, truncation=True, save_file=False)
        for index, spectrum in converted_truncated_df.iterrows():
            band = spectrum.xp
            ref = get_spectrum_with_source_id_and_xp(spectrum.source_id, band, ref_sampled_truncated)
            npt.assert_almost_equal(ref['flux'], spectrum.flux, decimal=TOL)
            npt.assert_almost_equal(ref['error'], spectrum.flux_error, decimal=TOL)


class TestConverterSamplingRange(unittest.TestCase):

    def test_sampling_equal(self):
        _, positions = convert(input_file, sampling=sampling, truncation=True, save_file=False)
        npt.assert_array_equal(sampling, positions)

    def test_sampling_low(self):
        with self.assertRaises(ValueError):
            convert(input_file, sampling=np.linspace(-15, 60, 600), save_file=False)

    def test_sampling_high(self):
        with self.assertRaises(ValueError):
            convert(input_file, sampling=np.linspace(-10, 71, 600), save_file=False)

    def test_sampling_both_wrong(self):
        with self.assertRaises(ValueError):
            convert(input_file, sampling=np.linspace(-11, 71, 600), save_file=False)

    def test_sampling_none(self):
        with self.assertRaises(ValueError):
            convert(input_file, sampling=None, save_file=False)


class TestConverterMissingBand(unittest.TestCase):

    def test_missing_band(self):
        missing_band_fits = join(continuous_path, 'XP_CONTINUOUS_RAW_missing_BP_votable_plain_dr3int6.xml')
        converted_spectra, sampling = convert(missing_band_fits, save_file=False)
        npt.assert_array_equal(sampling, np.linspace(0, 60, 600))
        converted_spectra = converted_spectra.iloc[0]
        # Read solution
        solution_values = pd.read_csv(missing_band_solution, float_precision='round_trip').iloc[0]
        self.assertEqual(converted_spectra['source_id'], solution_values['source_id'])
        self.assertEqual(converted_spectra['xp'], solution_values['xp'])
        npt.assert_array_almost_equal(converted_spectra['flux'], np.array(literal_eval(solution_values['flux'])))
        npt.assert_array_almost_equal(converted_spectra['flux_error'],
                                      np.array(literal_eval(solution_values['flux_error'])))
