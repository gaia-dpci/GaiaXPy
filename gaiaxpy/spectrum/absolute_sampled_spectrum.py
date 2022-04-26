"""
absolute_sampled_spectrum.py
====================================
Module to represent an absolute sampled spectrum.
"""

import numpy as np
from .sampled_spectrum import SampledSpectrum
from .utils import _list_to_array
from gaiaxpy.core.satellite import BANDS, BP_WL, RP_WL


class AbsoluteSampledSpectrum(SampledSpectrum):
    """
    A spectrum calibrated onto the absolute system of wavelength and flux.
    The spectrum is represented by a set of discrete measurements or samples.
    """

    def __init__(
            self,
            source_id,
            xp_spectra,  # This one indicates the bands present
            sampled_bases,
            merge,
            truncation=-1):
        """
        Initialise an absolute sampled spectrum.

        Args:
            source_id (str): Source identifier.
            xp_spectra (dict): A dictionary containing the BP and RP continuous
                spectra.
            sampled_bases (dict): The set of basis functions sampled onto
                the grid defining the resolution of the final sampled spectrum.
            merge (dict): The weighting factors for BP and RP sampled onto
                the grid defining the resolution of the final sampled spectrum.
            truncation (int): Number of bases to be used for this spectrum. The set of
                bases functions used for the continuous representation of the spectra
                has been optimised to ensure that the first bases are the ones that
                contribute most. In many cases, the last bases contribution will be below
                the noise. Truncation of the basis function set to preserve only the
                significant bases is optional. By default, no truncation will be applied,
                i.e. all bases will be used.
        """
        # Bands available
        bands = [band for band in xp_spectra.keys() if len(xp_spectra[band].get_coefficients()) != 0]

        if not bands:
            raise BaseException('At least one band must be present.')

        # If there at least one band present
        if len(bands) >= 1:
            pos = sampled_bases[bands[0]]._get_sampling_grid()
        else:
            raise BaseException('At least one band must be present.')

        SampledSpectrum.__init__(self, source_id, pos)

        split_spectrum = {band: {} for band in BANDS}
        for band in bands:
            if isinstance(truncation, (int, np.int64)) and truncation > 0:
                split_spectrum[band]['xp_spectra'] = xp_spectra[band]
                split_spectrum[band]['flux'] = self._sample_flux(
                    split_spectrum[band]['xp_spectra'].get_coefficients()[:truncation],
                    sampled_bases[band]._get_design_matrix()[:truncation][:])
                split_spectrum[band]['error'] = self._sample_error(
                    split_spectrum[band]['xp_spectra'].get_covariance()[
                        :truncation, :truncation],
                    sampled_bases[band]._get_design_matrix()[:truncation][:],
                    split_spectrum[band]['xp_spectra'].get_standard_deviation())
            else:
                split_spectrum[band]['xp_spectra'] = xp_spectra[band]
                split_spectrum[band]['flux'] = self._sample_flux(
                    split_spectrum[band]['xp_spectra'].get_coefficients(),
                    sampled_bases[band]._get_design_matrix())
                split_spectrum[band]['error'] = self._sample_error(
                    split_spectrum[band]['xp_spectra'].get_covariance(),
                    sampled_bases[band]._get_design_matrix(),
                    split_spectrum[band]['xp_spectra'].get_standard_deviation())

        # If both bands are present
        if len(bands) == 2:
            self.flux = np.add(
                np.multiply(
                    split_spectrum[BANDS.bp]['flux'], merge[BANDS.bp]), np.multiply(
                    split_spectrum[BANDS.rp]['flux'], merge[BANDS.rp]))
            self.error = np.sqrt(
                np.add(
                    np.multiply(
                        split_spectrum[BANDS.bp]['error']**2,
                        merge[BANDS.bp]**2),
                    np.multiply(
                        split_spectrum[BANDS.rp]['error']**2,
                        merge[BANDS.rp]**2)))
            self.pos = pos
        # If just one is
        elif len(bands) == 1:
            existing_band = bands[0]
            self.flux = split_spectrum[existing_band]['flux']
            self.error = split_spectrum[existing_band]['error']
            self.pos = pos
            # Patch values if there's a band missing
            masked_pos = self.pos.copy()
            masked_pos = masked_pos.astype(float)
            if existing_band == BANDS.rp:
                masked_pos[masked_pos <= RP_WL.low] = np.nan
            elif existing_band == BANDS.bp:
                masked_pos[masked_pos >= BP_WL.high] = np.nan
            # Get the indices of all the values in pos that are less than the lowest RP range value
            self.flux[np.argwhere(np.isnan(masked_pos))] = np.nan
            self.error[np.argwhere(np.isnan(masked_pos))] = np.nan
        else:
            raise BaseException("At least one band must be available.")

    def _get_fluxes(self):
        return self.flux

    def _get_flux_errors(self):
        return self.error

    def _get_positions(self):
        return self.pos

    @classmethod
    def _get_flux_label(cls):
        return 'Flux [W nm^-1 m^-2]'

    @classmethod
    def _get_position_label(cls):
        return 'Wavelength [nm]'

    def _spectrum_to_dict(self):
        """
        Represent the spectrum as a dictionary.

        Returns:
            dict: A dictionary populated with the minimum set of parameters that
                need to be stored for this object. This is optimised for writing
                large number of sampled spectra and for this reason the array of
                positions is NOT included as it is expected to be the same for
                a batch of spectra. The array of positions can be retrieved calling
                the sampling_to_dict method.
        """
        return {
            'source_id': self.source_id,
            'flux': _list_to_array(self.flux),
            'flux_error': _list_to_array(self.error)
        }

    def _sampling_to_dict(self):
        """
        Represent the sampling grid as a dictionary.

        Returns:
            dict: A dictionary populated with the sampling grid used for this spectrum.
        """
        return {
            'pos': _list_to_array(self.pos)
        }
