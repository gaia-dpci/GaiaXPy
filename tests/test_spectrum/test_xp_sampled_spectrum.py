import unittest

import numpy as np

from gaiaxpy.config.paths import hermite_bases_file
from gaiaxpy.converter.config import parse_config
from gaiaxpy.converter.converter import get_design_matrices
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from gaiaxpy.spectrum.generic_spectrum import Spectrum
from gaiaxpy.spectrum.sampled_spectrum import SampledSpectrum
from gaiaxpy.spectrum.utils import _correlation_to_covariance_dr3int5
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum
from gaiaxpy.spectrum.xp_sampled_spectrum import XpSampledSpectrum
from gaiaxpy.spectrum.xp_spectrum import XpSpectrum
from tests.files.paths import mean_spectrum_csv_file

parser = InternalContinuousParser(MANDATORY_INPUT_COLS['convert'] + CORR_INPUT_COLUMNS)
correlation_parsed_file, _ = parser.parse_file(mean_spectrum_csv_file)

parsed_config = parse_config(hermite_bases_file)

# Sampling grid
n_samples = 481
output_samples = np.linspace(0, 60, n_samples)

# Generate design matrices containing the basis functions sampled on the defined sampling grid.
design_matrices = get_design_matrices(output_samples, parsed_config)


class TestXpSampledSpectrum(unittest.TestCase):

    def test_init(self):
        # Create single BP and single RP spectrum
        row = correlation_parsed_file.head(1)
        for band in BANDS:
            correlation_matrix = row[f'{band}_coefficient_correlations'][0]
            parameters = row[f'{band}_coefficients'][0]
            standard_deviation = row[f'{band}_standard_deviation'][0]
            design_matrix = design_matrices.get(band)
            covariance_matrix = _correlation_to_covariance_dr3int5(correlation_matrix,
                                                                   row[f'{band}_coefficient_errors'][0],
                                                                   row[f'{band}_standard_deviation'][0])
            continuous_spectrum = XpContinuousSpectrum(row['source_id'][0], band, parameters, covariance_matrix,
                                                       standard_deviation)
            spectrum = XpSampledSpectrum.from_continuous(continuous_spectrum, design_matrix)
            self.assertIsInstance(spectrum, XpSampledSpectrum)
            self.assertIsInstance(spectrum, SampledSpectrum)
            self.assertIsInstance(spectrum, XpSpectrum)
            self.assertIsInstance(spectrum, Spectrum)
