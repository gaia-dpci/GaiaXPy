"""
synthetic_photometry_generator.py
====================================
Module for the generation of synthetic photometry.
"""

from configparser import ConfigParser

from gaiaxpy.config.paths import config_ini_file
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.single_synthetic_photometry import SingleSyntheticPhotometry
from gaiaxpy.spectrum.utils import get_covariance_matrix
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum

config_parser = ConfigParser()
config_parser.read(config_ini_file)


class SyntheticPhotometryGenerator(object):
    def generate(self, parsed_input_data, extension, output_file, output_format, save_file):
        raise ValueError('Method not defined for base class.')

    def _get_sampled_basis_functions(self, xp_sampling, xp_sampling_grid):
        return {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_sampling[band]) for band in BANDS}

    def _create_photometry_list(self, parsed_input_data, photometric_system, sampled_basis_func, xp_merge):
        parsed_input_data_dict = parsed_input_data.to_dict('records')
        return (_generate_synthetic_photometry(row, sampled_basis_func, xp_merge, photometric_system) for row in
                parsed_input_data_dict)


def _generate_synthetic_photometry(row, design_matrix, merge, photometric_system):
    """
    Create the synthetic photometry from the input continuously-represented mean spectrum and design matrix.

    Args:
        row (DataFrame): Single row in a DataFrame containing the entry for one source in the mean spectra file. This
            will include columns for both bands (although one could be missing).
        design_matrix (ndarray): 2D array containing the basis functions sampled for the specific photometric system.
        merge (dict): Dictionary containing an array of weights per BP and one for RP. These have one value per sample
            and define the contributions from BP and RP to the joined absolute spectrum.
        photometric_system (obj): Photometric system object containing the zero-points.

    Returns:
        SingleSyntheticPhotometry: The output synthetic photometry.
    """
    cont_dict = {band: XpContinuousSpectrum(row['source_id'], band.upper(), row[f'{band}_coefficients'],
                                            get_covariance_matrix(row, band), row[f'{band}_standard_deviation'])
                 for band in BANDS}
    return SingleSyntheticPhotometry(row['source_id'], cont_dict, design_matrix, merge, photometric_system)
