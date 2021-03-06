import unittest
import numpy as np
from configparser import ConfigParser
from os import path
from gaiaxpy.config import config_path
from gaiaxpy.converter import get_design_matrices, get_unique_basis_ids, load_config
from gaiaxpy.file_parser import InternalContinuousParser
from gaiaxpy.spectrum import _correlation_to_covariance_dr3int5, XpContinuousSpectrum, \
                             XpSampledSpectrum, SampledSpectrum, XpSpectrum, Spectrum
from gaiaxpy.core.satellite import BANDS
from tests.files import files_path

configparser = ConfigParser()
configparser.read(path.join(config_path, 'config.ini'))
config_file = path.join(config_path, configparser.get('converter', 'optimised_bases'))

# Files to test parse
csv_file_with_correlation = path.join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_dr3int6.csv')

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


class TestXpSampledSpectrum(unittest.TestCase):

    def test_init(self):
        # Create single BP and single RP spectrum
        row = correlation_parsed_file.head(1)
        for band in BANDS:
            correlation_matrix = row[f'{band}_coefficient_correlations'][0]
            parameters = row[f'{band}_coefficients'][0]
            standard_deviation = row[f'{band}_standard_deviation'][0]
            design_matrix = design_matrices.get(
                row[f'{band}_basis_function_id'][0])
            covariance_matrix = _correlation_to_covariance_dr3int5(
                correlation_matrix,
                row[f'{band}_coefficient_errors'][0],
                row[f'{band}_standard_deviation'][0])
            continuous_spectrum = XpContinuousSpectrum(row['source_id'][0],
                                                       band,
                                                       parameters,
                                                       covariance_matrix,
                                                       standard_deviation)

            spectrum = XpSampledSpectrum.from_continuous(
                continuous_spectrum,
                design_matrix)
            self.assertIsInstance(spectrum, XpSampledSpectrum)
            self.assertIsInstance(spectrum, SampledSpectrum)
            self.assertIsInstance(spectrum, XpSpectrum)
            self.assertIsInstance(spectrum, Spectrum)
