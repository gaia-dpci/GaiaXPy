"""
synthetic_photometry_generator.py
====================================
Module for the generation of synthetic photometry.
"""

from configparser import ConfigParser
from os import path

from gaiaxpy.config.paths import config_path
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.single_synthetic_photometry import SingleSyntheticPhotometry
from gaiaxpy.spectrum.utils import _get_covariance_matrix
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))


class SyntheticPhotometryGenerator(object):

    def _generate(input_object, photometric_system, output_file, output_format, save_file, bp_model='v375wi',
                  rp_model='v142r'):
        raise ValueError('Method not defined for base class.')

    def _get_sampled_basis_functions(self, xp_sampling, xp_sampling_grid):
        return {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_sampling[band]) for band in BANDS}

    def _create_photometry_list(self, parsed_input_data, photometric_system, sampled_basis_func, xp_merge):
        return (_generate_synthetic_photometry(row, sampled_basis_func, xp_merge, photometric_system) for index, row in
                parsed_input_data.iterrows())


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
    cont_dict = dict()
    for band in BANDS:
        covariance_matrix = _get_covariance_matrix(row, band)
        if covariance_matrix is not None:
            continuous_spectrum = XpContinuousSpectrum(row['source_id'], band.upper(), row[f'{band}_coefficients'],
                                                       covariance_matrix, row[f'{band}_standard_deviation'])
            cont_dict[band] = continuous_spectrum
    return SingleSyntheticPhotometry(row['source_id'], cont_dict, design_matrix, merge, photometric_system)
