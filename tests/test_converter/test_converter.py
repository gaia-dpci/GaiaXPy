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
from tests.files.paths import mean_spectrum_xml_plain_file, con_ref_sampled_csv_path, con_ref_sampled_truncated_csv_path,\
    mean_spectrum_avro_file, mean_spectrum_csv_file, mean_spectrum_ecsv_file, mean_spectrum_fits_file,\
    mean_spectrum_xml_file
from tests.test_converter.converter_paths import optimised_bases_df, converter_csv_solution_0_60_481_df
from tests.utils.utils import get_spectrum_with_source_id_and_xp, npt_array_err_message, is_instance_err_message

con_input_files = [mean_spectrum_avro_file, mean_spectrum_csv_file, mean_spectrum_ecsv_file, mean_spectrum_fits_file,
                   mean_spectrum_xml_file, mean_spectrum_xml_plain_file]

# Parsers
parser = InternalContinuousParser()

sampling = np.linspace(0, 60, 481)

sampled_parser = InternalSampledParser()
ref_sampled, _ = sampled_parser._parse(con_ref_sampled_csv_path)
ref_sampled_truncated, _ = sampled_parser._parse(con_ref_sampled_truncated_csv_path)

TOL = 4
_rtol, _atol = 1e-6, 1e-6  # Precision varies with extension


class TestGetMethods(unittest.TestCase):

    def test_get_unique_basis_ids(self):
        instance = set
        for file in con_input_files:
            parsed_input, _ = parser._parse(file)
            unique_bases_ids = get_unique_basis_ids(parsed_input)
            self.assertIsInstance(unique_bases_ids, instance, msg=is_instance_err_message(file, instance))
            self.assertEqual(unique_bases_ids, {56, 57})

    def test_get_design_matrices(self):
        instance = SampledBasisFunctions
        for file in con_input_files:
            parsed_input, _ = parser._parse(file)
            unique_bases_ids = get_unique_basis_ids(parsed_input)
            design_matrices = get_design_matrices(unique_bases_ids, sampling, optimised_bases_df)
            self.assertIsInstance(design_matrices, dict, msg=is_instance_err_message(file, dict))
            self.assertEqual(len(design_matrices), 2)
            self.assertEqual(list(design_matrices.keys()), [56, 57])
            self.assertIsInstance(design_matrices[56], instance, msg=is_instance_err_message(file, instance))
            self.assertIsInstance(design_matrices[57], instance, msg=is_instance_err_message(file, instance))


class TestCreateSpectrum(unittest.TestCase):

    def test_create_spectrum(self):
        spectrum = dict()
        truncation = True
        instance = XpSampledSpectrum
        for file in con_input_files:
            parsed_input, _ = parser._parse(file)
            parsed_input_dict = parsed_input.to_dict('records')
            unique_bases_ids = get_unique_basis_ids(parsed_input)
            design_matrices = get_design_matrices(unique_bases_ids, sampling, optimised_bases_df)
            for row in islice(parsed_input_dict, 1):  # Just the first row
                for band in BANDS:
                    spectrum[band] = _create_spectrum(row, truncation, design_matrices, band)
            self.assertEqual(spectrum[BANDS.bp].get_source_id(), spectrum[BANDS.rp].get_source_id())
            for band in BANDS:
                self.assertIsInstance(spectrum[band], instance, msg=is_instance_err_message(file, instance, band))
                self.assertEqual(spectrum[band].get_xp(), band)


class TestConverter(unittest.TestCase):

    def test_converter_both_types(self):
        for file in con_input_files:
            converted_df, _ = convert(file, sampling=sampling, save_file=False)
            self.assertIsInstance(converted_df, pd.DataFrame)
            self.assertEqual(len(converted_df), 4)
            pdt.assert_frame_equal(converted_df, converter_csv_solution_0_60_481_df, rtol=1e-6, atol=1e-6)

    def test_conversion(self):
        for file in con_input_files:
            converted_df, _ = convert(file, sampling=sampling, save_file=False)
            for spectrum in converted_df.to_dict('records'):
                ref = get_spectrum_with_source_id_and_xp(spectrum['source_id'], spectrum['xp'], ref_sampled)
                npt.assert_almost_equal(ref['flux'], spectrum['flux'], decimal=TOL)
                npt.assert_almost_equal(ref['error'], spectrum['flux_error'], decimal=TOL)


class TestTruncation(unittest.TestCase):

    def test_truncation(self):
        for file in con_input_files:
            converted_truncated_df, _ = convert(file, sampling=sampling, truncation=True, save_file=False)
            for spectrum in converted_truncated_df.to_dict('records'):
                ref = get_spectrum_with_source_id_and_xp(spectrum['source_id'], spectrum['xp'], ref_sampled_truncated)
                npt.assert_almost_equal(ref['flux'], spectrum['flux'], decimal=TOL, err_msg=npt_array_err_message(file))
                npt.assert_almost_equal(ref['error'], spectrum['flux_error'], decimal=TOL,
                                        err_msg=npt_array_err_message(file))


class TestConverterSamplingRange(unittest.TestCase):

    def test_sampling_equal(self):
        for file in con_input_files:
            _, _positions = convert(file, sampling=sampling, truncation=True, save_file=False)
            npt.assert_array_equal(sampling, _positions)

    def test_sampling_low(self):
        for file in con_input_files:
            with self.assertRaises(ValueError):
                convert(file, sampling=np.linspace(-15, 60, 600), save_file=False)

    def test_sampling_high(self):
        for file in con_input_files:
            with self.assertRaises(ValueError):
                convert(file, sampling=np.linspace(-10, 71, 600), save_file=False)

    def test_sampling_both_wrong(self):
        for file in con_input_files:
            with self.assertRaises(ValueError):
                convert(file, sampling=np.linspace(-11, 71, 600), save_file=False)

    def test_sampling_none(self):
        for file in con_input_files:
            with self.assertRaises(ValueError):
                convert(file, sampling=None, save_file=False)
