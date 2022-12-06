import unittest
from configparser import ConfigParser
from os import path

import numpy as np

from gaiaxpy.config.paths import config_path
from gaiaxpy.converter.config import load_config
from gaiaxpy.converter.converter import get_design_matrices, get_unique_basis_ids
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.generic_spectrum import Spectrum
from gaiaxpy.spectrum.utils import _correlation_to_covariance_dr3int4
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum
from gaiaxpy.spectrum.xp_spectrum import XpSpectrum
from tests.files.paths import files_path

configparser = ConfigParser()
configparser.read(path.join(config_path, 'config.ini'))
config_file = path.join(config_path, configparser.get('converter', 'optimised_bases'))

# Files to test parse
csv_file_with_correlation = path.join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW.csv')

parser = InternalContinuousParser()
correlation_parsed_file, _ = parser.parse(csv_file_with_correlation)

parsed_config = load_config(config_file)

# Sampling grid
n_samples = 481
output_samples = np.linspace(0, 60, n_samples)

# Get unique basis set for both bands
unique_bases_ids = get_unique_basis_ids(correlation_parsed_file)
# Generate design matrices containing the basis functions sampled on the
# defined sampling grid.
design_matrices = get_design_matrices(
    unique_bases_ids, output_samples, parsed_config)


class TestXpContinuousSpectrum(unittest.TestCase):

    def test_init(self):
        # Create single BP and single RP spectrum
        row = correlation_parsed_file.head(1)
        for band in BANDS:
            correlation_matrix = row[f'{band}_coefficient_correlations'][0]
            parameters = row[f'{band}_coefficients'][0]
            standard_deviation = row[f'{band}_standard_deviation'][0]
            covariance_matrix = _correlation_to_covariance_dr3int4(
                correlation_matrix,
                row[f'{band}_coefficient_errors'][0],
                row[f'{band}_standard_deviation'][0])
            continuous_spectrum = XpContinuousSpectrum(row['source_id'][0],
                                                       band,
                                                       parameters,
                                                       covariance_matrix,
                                                       standard_deviation)
            self.assertIsInstance(continuous_spectrum, XpContinuousSpectrum)
            self.assertIsInstance(continuous_spectrum, XpSpectrum)
            self.assertIsInstance(continuous_spectrum, Spectrum)
