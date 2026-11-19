"""Provide shared basis preparation and single-source photometry construction.

Generation uses passband integration matrices stored in each filter file rather
than first sampling a calibrated spectrum on a wavelength grid.
"""

import yaml

from gaiaxpy.config.paths import config_yaml_file
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.single_synthetic_photometry import SingleSyntheticPhotometry
from gaiaxpy.spectrum.utils import get_covariance_matrix
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum

with open(config_yaml_file) as f:
    config_parser = yaml.safe_load(f)


class SyntheticPhotometryGenerator:
    """Define the generation interface and shared design-matrix preparation."""

    def generate(self, parsed_input_data, truncation, disable_info=False):
        """Reject direct generation through the base class.

        Subclasses implement this interface. Direct use raises ValueError.
        """
        raise ValueError('Method not defined for base class.')

    def _get_sampled_basis_functions(self, xp_sampling, xp_sampling_grid):
        """Wrap the BP/RP integration matrices as SampledBasisFunctions.

        Args:
            xp_sampling (dict): BP and RP matrices keyed by 'bp' and 'rp', with
                basis functions along rows and passbands along columns.
            xp_sampling_grid (array-like): Filter sampling associated with the
                matrix columns, in passband order.

        Returns:
            dict: SampledBasisFunctions objects keyed by photometer.
        """
        return {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_sampling[band]) for band in BANDS}


def _generate_synthetic_photometry(row, design_matrix, merge, truncation, photometric_system):
    """Construct photometry for one source and one selected system.

    Args:
        row (pandas.Series or mapping): Source fields accessed by column name,
            including BP/RP coefficients, coefficient errors and correlations,
            standard deviations and, when truncating, relevant-basis counts.
        design_matrix (dict): Per-photometer SampledBasisFunctions describing
            passband integration, keyed by 'bp' and 'rp'.
        merge (dict): BP/RP contribution weights in passband order.
        truncation (bool): True passes this source's bp_n_relevant_bases for BP
            and rp_n_relevant_bases for RP. False uses all available functions.
        photometric_system (PhotometricSystem): Selected system supplying zero
            points and flux-bias corrections.

    Returns:
        SingleSyntheticPhotometry: Source photometry after configured flux-bias
        corrections and magnitude conversion. Later pipeline stages handle
        colour equations, tabulated flux-error correction and polynomial
        standardisation.
    """
    cont_dict = {band: XpContinuousSpectrum(row['source_id'], band.upper(), row[f'{band}_coefficients'],
                                            get_covariance_matrix(row, band), row[f'{band}_standard_deviation'])
                 for band in BANDS}
    truncation = {band: row[f'{band}_n_relevant_bases'] for band in BANDS} if truncation else None
    return SingleSyntheticPhotometry(row['source_id'], cont_dict, design_matrix, merge, truncation, photometric_system)
