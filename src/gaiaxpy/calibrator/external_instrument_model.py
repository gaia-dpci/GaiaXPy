"""
external_instrument_model.py
====================================
Module for handling the various components of the external calibration instrument model.
These are dispersion function, instrument response and set of inverse bases.
"""

import numpy as np
import pandas as pd
from scipy import interpolate

from gaiaxpy.file_parser.parse_inverse import InverseBasesParser


class ExternalInstrumentModel(object):
    """
    External calibration instrument model.
    """

    def __init__(self, dispersion: dict, response: dict, bases: pd.DataFrame):
        """
        Initialise an external instrument model.

        Args:
            dispersion (dict): A dictionary contained the dispersion function sampled on a high resolution grid
                (simple spline interpolation will be used to estimate the dispersion at different locations).
            response (dict): A dictionary containing the response curve sampled on a high resolution grid (simple spline
                interpolation will be used to estimate the dispersion at different locations).
            bases (DataFrame): A DataFrame containing the definition of the inverse bases, required to reconstruct the
                absolute spectrum.
        """
        self.dispersion = dispersion
        self.response = response
        self.bases = bases

    @classmethod
    def from_config_csv(cls, dispersion_path: str, response_path: str, bases_path: str):
        """
        Create an external calibration instrument model from the input configuration files.

        Args:
            dispersion_path (str): Path to the configuration file containing the dispersion.
            response_path (str): Path to the configuration file containing the response.
            bases_path (str): Path to the configuration file containing the inverse bases.

        Returns:
            ExternalInstrumentModel: An external calibration instrument model object.
        """
        # Dispersion
        _disp = np.genfromtxt(dispersion_path, delimiter=',')
        dispersion = dict(zip(['wavelength', 'pseudo-wavelength'], [_disp[0], _disp[1]]))
        # Response
        _resp = np.genfromtxt(response_path, delimiter=',')
        response = dict(zip(['wavelength', 'response'], [_resp[0], _resp[1]]))
        # Bases
        bases, _ = InverseBasesParser().parse_file(bases_path)
        bases = bases.iloc[0]
        bases['inverseBasesCoefficients'] = bases['inverseBasesCoefficients'].reshape(bases['nBases'],
                                                                                      bases['nInverseBasesCoefficients'])
        bases['transformationMatrix'] = bases['transformationMatrix'].reshape(bases['nBases'], bases['nTransformedBases'])
        return cls(dispersion, response, bases)

    def get_response(self, wavelength: float) -> np.ndarray:
        """
        Get the response of the mean instrument at a certain wavelength.

        Args:
            wavelength (float): The absolute wavelength.

        Returns:
            ndarray: The response of the mean instrument at the input wavelength.
        """
        tck = interpolate.splrep(self.response.get("wavelength"), self.response.get("response"), s=0)
        return interpolate.splev(wavelength, tck, der=0)

    def wl_to_pwl(self, wavelength: float) -> np.ndarray:
        """
        Convert the input absolute wavelength to a pseudo-wavelength.

        Args:
            wavelength (float): Absolute wavelength.

        Returns:
            ndarray: The corresponding pseudo-wavelength value.
        """
        tck = interpolate.splrep(self.dispersion.get("wavelength"), self.dispersion.get("pseudo-wavelength"), s=0)
        return interpolate.splev(wavelength, tck, der=0)
