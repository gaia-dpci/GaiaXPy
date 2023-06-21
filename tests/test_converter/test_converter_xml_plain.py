import unittest
from ast import literal_eval
from itertools import islice

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import convert
from gaiaxpy.converter.converter import _create_spectrum, get_design_matrices, get_unique_basis_ids
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.file_parser.parse_internal_sampled import InternalSampledParser
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.xp_sampled_spectrum import XpSampledSpectrum
from tests.files.paths import missing_bp_xml_plain_file, mean_spectrum_xml_plain_file
from tests.test_converter.converter_paths import ref_sampled_csv, ref_sampled_truncated_csv,\
    converter_csv_solution_0_60_481_df, missing_band_sampling_solution_path, optimised_bases_df
from tests.utils.utils import get_spectrum_with_source_id_and_xp

# Parsers
parser = InternalContinuousParser()
# Parsed files
parsed_input, _ = parser._parse(mean_spectrum_xml_plain_file)

sampling = np.linspace(0, 60, 481)
unique_bases_ids = get_unique_basis_ids(parsed_input)
design_matrices = get_design_matrices(unique_bases_ids, sampling, optimised_bases_df)

converted_df, _ = convert(mean_spectrum_xml_plain_file, sampling=sampling, save_file=False)

sampled_parser = InternalSampledParser()
ref_sampled, _ = sampled_parser._parse(ref_sampled_csv)
ref_sampled_truncated, _ = sampled_parser._parse(ref_sampled_truncated_csv)

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
        parsed_input_dict = parsed_input.to_dict('records')
        spectrum_bp, spectrum_rp = None, None
        for row in islice(parsed_input_dict, 1):  # Just the first row
            spectrum_bp = _create_spectrum(row, truncation, design_matrices, BANDS.bp)
            spectrum_rp = _create_spectrum(row, truncation, design_matrices, BANDS.rp)
        self.assertIsInstance(spectrum_bp, XpSampledSpectrum)
        self.assertIsInstance(spectrum_rp, XpSampledSpectrum)
        self.assertEqual(spectrum_bp.get_source_id(), spectrum_rp.get_source_id())
        self.assertEqual(spectrum_bp.get_xp(), BANDS.bp)
        self.assertEqual(spectrum_rp.get_xp(), BANDS.rp)


class TestConverter(unittest.TestCase):

    def test_converter_both_types(self):
        self.assertIsInstance(converted_df, pd.DataFrame)
        self.assertEqual(len(converted_df), 4)
        pdt.assert_frame_equal(converted_df, converter_csv_solution_0_60_481_df, rtol=_rtol, atol=_atol)

    def test_conversion(self):
        for spectrum in converted_df.to_dict('records'):
            ref = get_spectrum_with_source_id_and_xp(spectrum['source_id'], spectrum['xp'], ref_sampled)
            npt.assert_almost_equal(ref['flux'], spectrum['flux'], decimal=TOL)
            npt.assert_almost_equal(ref['error'], spectrum['flux_error'], decimal=TOL)


class TestTruncation(unittest.TestCase):

    def test_truncation(self):
        converted_truncated_df, _ = convert(mean_spectrum_xml_plain_file, sampling=sampling, truncation=True,
                                            save_file=False)
        for spectrum in converted_truncated_df.to_dict('records'):
            ref = get_spectrum_with_source_id_and_xp(spectrum['source_id'], spectrum['xp'], ref_sampled_truncated)
            npt.assert_almost_equal(ref['flux'], spectrum['flux'], decimal=TOL)
            npt.assert_almost_equal(ref['error'], spectrum['flux_error'], decimal=TOL)


class TestConverterSamplingRange(unittest.TestCase):

    def test_sampling_equal(self):
        _, _positions = convert(mean_spectrum_xml_plain_file, sampling=sampling, truncation=True, save_file=False)
        npt.assert_array_equal(sampling, _positions)

    def test_sampling_low(self):
        with self.assertRaises(ValueError):
            convert(mean_spectrum_xml_plain_file, sampling=np.linspace(-15, 60, 600), save_file=False)

    def test_sampling_high(self):
        with self.assertRaises(ValueError):
            convert(mean_spectrum_xml_plain_file, sampling=np.linspace(-10, 71, 600), save_file=False)

    def test_sampling_both_wrong(self):
        with self.assertRaises(ValueError):
            convert(mean_spectrum_xml_plain_file, sampling=np.linspace(-11, 71, 600), save_file=False)

    def test_sampling_none(self):
        with self.assertRaises(ValueError):
            convert(mean_spectrum_xml_plain_file, sampling=None, save_file=False)


class TestConverterMissingBand(unittest.TestCase):

    def test_missing_band(self):
        converted_spectra, sampling = convert(missing_bp_xml_plain_file, save_file=False)
        npt.assert_array_equal(sampling, np.linspace(0, 60, 600))
        converted_spectra = converted_spectra.iloc[0]
        # Read solution
        solution_values = pd.read_csv(missing_band_sampling_solution_path, float_precision='high').iloc[0]
        self.assertEqual(converted_spectra['source_id'], solution_values['source_id'])
        self.assertEqual(converted_spectra['xp'], solution_values['xp'])
        npt.assert_array_almost_equal(converted_spectra['flux'], np.array(literal_eval(solution_values['flux'])))
        npt.assert_array_almost_equal(converted_spectra['flux_error'],
                                      np.array(literal_eval(solution_values['flux_error'])))
