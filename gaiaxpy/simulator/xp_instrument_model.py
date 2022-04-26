"""
xp_instrument_model.py
====================================
Module for the instrument model of the simulator.
"""

import numpy as np

class XpInstrumentModel:
    """
    XP instrument model.
    """

    def __init__(self,
                 al,
                 wl,
                 kernel,
                 ensamble_kernels):
        """
        Initialise an xp instrument model.

        Args:
        al (ndarray): AL pseudo-wavelength sampling grid.
        wl (ndarray): Wavelength sampling grid.
        kernel (ndarray): Instrument model kernel.
        ensambleKernels (list): List of ensamble matrices (as ndarray) containing the difference between each ensamble
            model and the mean model.
        """
        self.al = al
        self.wl = wl
        self.kernel = kernel
        self.kernel2 = np.square(kernel)
        self.ensamble_kernels = ensamble_kernels

    def get_al(self):
        return self.al

    def get_wl(self):
        return self.wl

    def get_kernel(self):
        return self.kernel

    def get_ensamble_kernels(self):
        return self.ensamble_kernels

    def get_flux(self, flux):
        """
        Get the flux for each sample in the pseudo-wavelength grid.

        Args:
            flux (ndarray): Photon flux distribution sampled on the current model wavelength grid.

        Returns:
            ndarray: The flux for each sample.
        """
        return self.kernel.dot(flux)  # originally using Java's Vector 'operate' method

    def get_flux_error(self, flux, error):
        """
        Get the flux error for each sample in the pseudo-wavelength grid. This includes contributions from the model and
        SED errors.

        Args:
            flux (ndarray): Photon flux distribution sampled on the current model wavelength grid.
            error (ndarray): Error on the SED fluxes.
        Returns:
            ndarray: The flux error for each sample.
        """
        return np.sqrt(np.square(self.get_model_error(flux)) + np.square(self.get_sed_error(error)))

    def get_model_error(self, flux):
        """
        Get the flux error for each sample in the pseudo-wavelength grid. This method only accounts for model errors.

        Args:
            flux (ndarray): Photon flux distribution sampled on the current model wavelength grid.

        Returns:
            ndarray: The flux error for each sample.
        """
        error = np.zeros(len(self.al))
        for ensamble_kernel in self.ensamble_kernels:
            np.add(error, np.square(ensamble_kernel.dot(flux)))

        n_ensamble = len(self.ensamble_kernels)
        np.divide(error, n_ensamble - 1.0)
        return np.sqrt(error)

    def get_covariance(self, flux):
        """
        Get the covariance matrix for the sampled spectrum.

        Args:
            ndarray (flux): Photon flux distribution sampled on the current model wavelength grid.

        Returns:
            ndarray: The covariance matrix.
        """
        cov = np.zeros([len(self.al), len(self.al)])
        for ensamble_kernel in self.ensamble_kernels:
            v = ensamble_kernel.dot(flux)
            np.add(cov, np.outer(v, v))

        n_ensamble = len(self.ensamble_kernels)
        np.divide(cov, n_ensamble - 1.0)
        return cov

    def get_sed_error(self, error):
        """
        Get the flux error for each sample in the pseudo-wavelength grid due to the propagation of the original SED errors.

        Args:
            flux (ndarray): Photon flux distribution sampled on the current model wavelength grid.

        Returns:
            ndarray: The flux error for each sample.
        """
        return np.sqrt(self.kernel2.dot(np.square(error)))