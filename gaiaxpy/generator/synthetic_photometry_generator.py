"""
synthetic_photometry_generator.py
====================================
Module for the generation of synthetic photometry.
"""

from configparser import ConfigParser
from os import path
from .photometric_system import _system_is_standard
from .regular_photometric_system import RegularPhotometricSystem
from .standardised_photometric_system import StandardisedPhotometricSystem
from gaiaxpy.config import config_path
from gaiaxpy.core import _progress_tracker
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum import _get_covariance_matrix, SampledBasisFunctions, \
                             SingleSyntheticPhotometry, XpContinuousSpectrum

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))


class SyntheticPhotometryGenerator(object):

    def _generate(input_object, photometric_system, output_file, output_format, save_file,
                  bp_model='v375wi', rp_model='v142r'):
        raise ValueError('Method not defined for base class.')

    def _get_sampled_basis_functions(self, xp_sampling, xp_sampling_grid):
        sampled_basis_func = {}
        for band in BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(
                xp_sampling_grid, xp_sampling[band])
        return sampled_basis_func

    def _create_photometry_list(self, parsed_input_data, photometric_system, sampled_basis_func, xp_merge):
        photometry_list = []
        nrows = len(parsed_input_data)

        @_progress_tracker
        def generate_synthetic_photometry(row, *args):
            sampled_basis_func, xp_merge, photometric_system = args[0], args[1], args[2]
            synthetic_photometry = _generate_synthetic_photometry(
                row, sampled_basis_func, xp_merge, photometric_system)
            photometry_list.append(synthetic_photometry)
        for index, row in parsed_input_data.iterrows():
            generate_synthetic_photometry(row, sampled_basis_func, xp_merge, photometric_system, index, nrows)
        return photometry_list


def _generate_synthetic_photometry(
        row,
        design_matrix,
        merge,
        photometric_system):
    """
    Create the synthetic photometry from the input continuously-represented
    mean spectrum and design matrix.

    Args:
        row (DataFrame): Single row in a DataFrame containing the entry
            for one source in the mean spectra file. This will include columns for
            both bands (although one could be missing).
        design_matrix (ndarray): 2D array containing the basis functions
            sampled for the specific photometric system.
        merge (dict): Dictionary containing an array of weights per BP and one for RP.
            These have one value per sample and define the contributions from BP and RP
            to the joined absolute spectrum.
        photometric_system (obj): Photometric system object containing the zero-points.

    Returns:
        SingleSyntheticPhotometry: The output synthetic photometry.
    """
    cont_dict = {}
    for band in BANDS:
        covariance_matrix = _get_covariance_matrix(row, band)
        if covariance_matrix is not None:
            continuous_spectrum = XpContinuousSpectrum(
                row['source_id'],
                band.upper(),
                row[f'{band}_coefficients'],
                covariance_matrix,
                row[f'{band}_standard_deviation'])
            cont_dict[band] = continuous_spectrum
    # Get the PhotometricSystem object
    system_label = photometric_system.get_system_label()
    if _system_is_standard(system_label):
        photometric_system = StandardisedPhotometricSystem(system_label)
    else:
        photometric_system = RegularPhotometricSystem(system_label)
    return SingleSyntheticPhotometry(row['source_id'],
                                     cont_dict,
                                     design_matrix,
                                     merge,
                                     photometric_system)
