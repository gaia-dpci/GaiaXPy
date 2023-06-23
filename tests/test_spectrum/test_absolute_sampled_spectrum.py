import unittest
from configparser import ConfigParser

from gaiaxpy.config.paths import config_ini_file
from gaiaxpy.core.config import load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.utils import _correlation_to_covariance_dr3int5
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum
from tests.files.paths import mean_spectrum_csv_file

configparser = ConfigParser()
configparser.read(config_ini_file)

label = 'calibrator'

xp_sampling_grid, xp_merge = load_xpmerge_from_xml()
xp_design_matrices = load_xpsampling_from_xml()

parser = InternalContinuousParser()
parsed_correlation, _ = parser._parse(mean_spectrum_csv_file)

# Create sampled basis functions
sampled_basis_func = {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_design_matrices[band])
                      for band in BANDS}


class TestAbsoluteSampledSpectrum(unittest.TestCase):

    def test_init_truncation(self):
        truncations = [{}, {'bp': 50, 'rp': 40}]
        for truncation in truncations:
            parsed_correlation_dict = parsed_correlation.to_dict('records')
            for row in parsed_correlation_dict:
                source_id = row['source_id']
                cont_dict = {}
                # Split both bands
                for _band in BANDS:
                    covariance_matrix = _correlation_to_covariance_dr3int5(row[f'{_band}_coefficient_correlations'],
                                                                           row[f'{_band}_coefficient_errors'],
                                                                           row[f'{_band}_standard_deviation'])
                    continuous_object = XpContinuousSpectrum(source_id, _band, row[f'{_band}_coefficients'],
                                                             covariance_matrix, row[f'{_band}_standard_deviation'])
                    cont_dict[_band] = continuous_object
                spectrum = AbsoluteSampledSpectrum(source_id, cont_dict, sampled_basis_func, xp_merge,
                                                   truncation=truncation)
                self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)
