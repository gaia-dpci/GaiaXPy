import unittest
from configparser import ConfigParser
from os import path
from gaiaxpy.config import config_path
from gaiaxpy.core import _load_xpmerge_from_csv, _load_xpsampling_from_csv
from gaiaxpy.file_parser import InternalContinuousParser
from gaiaxpy.spectrum import _correlation_to_covariance_dr3int5, AbsoluteSampledSpectrum, \
                             SampledBasisFunctions, XpContinuousSpectrum
from gaiaxpy.core.satellite import BANDS
from tests.files import files_path

configparser = ConfigParser()
configparser.read(path.join(config_path, 'config.ini'))

label = 'calibrator'

xp_sampling_grid, xp_merge = _load_xpmerge_from_csv(label)
xp_design_matrices = _load_xpsampling_from_csv(label)

parser = InternalContinuousParser()
file_to_parse = path.join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_dr3int6.csv')
parsed_correlation, _ = parser.parse(file_to_parse)

# Create sampled basis functions
sampled_basis_func = {}
for band in BANDS:
    sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(
        xp_sampling_grid, xp_design_matrices[band])


class TestAbsoluteSampledSpectrum(unittest.TestCase):

    def test_init(self):
        for index, row in parsed_correlation.iterrows():
            source_id = row['source_id']
            cont_dict = {}
            # Split both bands
            for band in BANDS:
                covariance_matrix = _correlation_to_covariance_dr3int5(
                    row[f'{band}_coefficient_correlations'],
                    row[f'{band}_coefficient_errors'],
                    row[f'{band}_standard_deviation'])
                continuous_object = XpContinuousSpectrum(
                    source_id,
                    band,
                    row[f'{band}_coefficients'],
                    covariance_matrix,
                    row[f'{band}_standard_deviation'])
                cont_dict[band] = continuous_object
            spectrum = AbsoluteSampledSpectrum(
                source_id, cont_dict, sampled_basis_func, xp_merge)
            self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)
