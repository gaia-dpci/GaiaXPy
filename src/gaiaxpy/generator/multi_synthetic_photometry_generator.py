"""Evaluate selected photometric systems for every source in an input table.

Prepare each filter's integration matrices once, reconstruct each source's
continuous BP/RP spectra, and collect the resulting passband photometry.
"""
from sys import stdout

import numpy as np
from tqdm import tqdm

from gaiaxpy.core.generic_variables import pbar_colour, pbar_units, pbar_message
from gaiaxpy.spectrum.multi_synthetic_photometry import MultiSyntheticPhotometry
from .synthetic_photometry_generator import SyntheticPhotometryGenerator
from ..core.config import load_xpsampling_from_file, load_xpmerge_from_file
from ..core.satellite import BANDS
from ..photometric_system.photometric_system import _system_is_standard
from ..spectrum.single_synthetic_photometry import SingleSyntheticPhotometry
from ..spectrum.utils import get_covariance_matrix
from ..spectrum.xp_continuous_spectrum import XpContinuousSpectrum


class MultiSyntheticPhotometryGenerator(SyntheticPhotometryGenerator):
    """Generate multiple systems while recording their filter files and flux-bias steps.

    Colour equations, tabulated flux-error correction, output metadata and saving
    are handled by the calling generation pipeline.
    """

    def __init__(self, photometric_system):
        """Store a non-empty system selection and initialise file/correction records.

        Args:
            photometric_system (list): Selected photometric-system members or
                internal views of built-in configurations.

        Raises:
            ValueError: The selection is empty.
        """
        if not photometric_system:
            raise ValueError('Photometric system list cannot be empty.')
        self.function_label = 'photsystem'
        self.photometric_system = photometric_system
        self.system_files = []
        self.standardisations = []

    def generate(self, parsed_input_data, truncation, disable_info=False):
        """Evaluate all selected passbands for each source in table order.

        Args:
            parsed_input_data (pandas.DataFrame): Prepared continuous spectra with
                coefficient errors, correlations and standard deviations. Relevant
                basis counts are required when truncation is enabled.
            truncation (bool): True uses each row's bp_n_relevant_bases for BP and
                rp_n_relevant_bases for RP. False uses all available functions.
            disable_info (bool): Suppress the per-source progress bar.

        Returns:
            pandas.DataFrame: source_id and scalar magnitude, flux and flux-error
            columns for each system/passband, in input source order. Additional
            systems retain their versioned labels.
        """
        __FUNCTION_KEY = 'photometry'

        systems = self.photometric_system
        systems_context = self.create_systems_context(systems)

        photometries = []

        for row in tqdm(parsed_input_data.itertuples(index=False), desc=pbar_message[__FUNCTION_KEY],
                        total=len(parsed_input_data), unit=pbar_units[__FUNCTION_KEY], leave=False,
                        colour=pbar_colour, file=stdout, disable=disable_info):
            cont_dict = self._build_continuous_spectra(row)
            source_truncation = ({band: getattr(row, f'{band}_n_relevant_bases') for band in BANDS}
                                 if truncation else None)

            source_id = getattr(row, 'source_id')
            source_photometries = [SingleSyntheticPhotometry(source_id, cont_dict, sampled_basis,
                                                             xp_merge, source_truncation, system)
                                   for system, sampled_basis, xp_merge in systems_context]
            photometries.append(source_photometries)

        return MultiSyntheticPhotometry(systems, photometries).generate_output_df()

    def create_systems_context(self, systems) -> list:
        """Load per-system matrices and weights, and reset filter/correction records.

        Args:
            systems (list): Selected system members or internal built-in views.

        Returns:
            list[tuple]: Each tuple contains the system, its BP/RP sampled integration
            matrices and merge weights.
        """
        system_contexts = []
        self.system_files = []
        self.standardisations = []
        for system in systems:
            system_file = system.value.get_system_file()
            xp_sampling = load_xpsampling_from_file(system_file)
            xp_sampling_grid, xp_merge = load_xpmerge_from_file(system_file)

            sampled_basis = self._get_sampled_basis_functions(xp_sampling, xp_sampling_grid)
            system_contexts.append((system, sampled_basis, xp_merge))
            self.system_files.append((system, system_file))
            if _system_is_standard(system.value.name) and np.any(system.get_offsets() != 0):
                self.standardisations.append({'system': system.get_system_full_label(),
                                              'method': 'flux_bias', 'file': system_file})
        return system_contexts

    @staticmethod
    def _build_continuous_spectra(row):
        """Reconstruct a source's continuous BP/RP spectra from an input row.

        Args:
            row (namedtuple): DataFrame row exposing source_id and per-photometer
                coefficients, coefficient errors, correlations and standard deviation.

        Returns:
            dict: XpContinuousSpectrum objects keyed by 'bp' and 'rp'. Covariance
            matrices are reconstructed from the row's error and correlation fields.
        """
        source_id = getattr(row, 'source_id')
        return {
            band: XpContinuousSpectrum(
                source_id,
                band.upper(),
                getattr(row, f'{band}_coefficients'),
                get_covariance_matrix(row, band),
                getattr(row, f'{band}_standard_deviation'))
            for band in BANDS
        }
