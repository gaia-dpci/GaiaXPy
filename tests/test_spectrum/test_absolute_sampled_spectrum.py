import unittest
from configparser import ConfigParser
from os import path

from gaiaxpy.config.paths import config_path
from gaiaxpy.core.config import _load_xpmerge_from_xml, _load_xpsampling_from_xml
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.utils import _correlation_to_covariance_dr3int5
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum
from tests.files.paths import files_path

configparser = ConfigParser()
configparser.read(path.join(config_path, 'config.ini'))

label = 'calibrator'

xp_sampling_grid, xp_merge = _load_xpmerge_from_xml()
xp_design_matrices = _load_xpsampling_from_xml()

parser = InternalContinuousParser()
file_to_parse = path.join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW.csv')
parsed_correlation, _ = parser.parse(file_to_parse)

# Create sampled basis functions
sampled_basis_func = {}
for band in BANDS:
    sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_design_matrices[band])


class TestAbsoluteSampledSpectrum(unittest.TestCase):

    def test_init_no_truncation(self):
        for index, row in parsed_correlation.iterrows():
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
            spectrum = AbsoluteSampledSpectrum(source_id, cont_dict, sampled_basis_func, xp_merge, truncation={})
            self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_init_truncation(self):
        for index, row in parsed_correlation.iterrows():
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
                                               truncation={'bp': 50, 'rp': 40})
            self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)
