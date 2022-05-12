"""
spectral_energy_distribution.py
====================================
Module to represent a spectral energy distribution (SED).
"""

from .sampled_spectrum import SampledSpectrum


class SpectralEnergyDistribution(SampledSpectrum):
    """
    A spectral energy distribution.
    """

    def __init__(
            self,
            source_id,
            wl,
            flux):

        SampledSpectrum.__init__(self, source_id, wl)
        self.flux = flux
