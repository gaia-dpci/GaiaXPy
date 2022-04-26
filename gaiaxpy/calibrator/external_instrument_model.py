"""
external_instrument_model.py
====================================
Module for handling the various components of the external calibration instrument model.
These are dispersion function, instrument response and set of inverse bases.
"""

import numpy as np
from scipy import interpolate
from gaiaxpy.file_parser import GenericParser


class ExternalInstrumentModel(object):
    """
    External calibration instrument model.
    """

    def __init__(self,
                 dispersion,
                 response,
                 bases):
        """
        Initialise a external instrument model.

        Args:
        dispersion (dict): A dictionary contained the dispersion function
            sampled on a high resolution grid (simple spline interpolation will be used to
            estimate the dispersion at different locations).
        response (dict): A dictionary containing the response curve
            sampled on a high resolution grid (simple spline interpolation will be used to
            estimate the dispersion at different locations).
        bases (DataFrame): A DataFrame containing the definition of the inverse bases,
            required to reconstruct the absolute spectrum.
        """
        self.dispersion = dispersion
        self.response = response
        self.bases = bases

    @classmethod
    def from_config_csv(cls, dispersion_path, response_path, bases_path):
        """
        Create an external calibration instrument model from the input configuration files.

        Args:
            dispersion_path (str): Path to the configuration file containing the dispersion.
            response_path (str): Path to the configuration file containing the response.
            bases_path (str): Path to the configuration file containing the inverse bases.

        Returns:
            obj: An external calibration instrument model object.
        """
        # Dispersion
        _disp = np.genfromtxt(dispersion_path, delimiter=',')
        dispersion = dict(
            zip(['wavelength', 'pseudo-wavelength'], [_disp[0], _disp[1]]))

        # Response
        _resp = np.genfromtxt(response_path, delimiter=',')
        response = dict(zip(['wavelength', 'response'], [_resp[0], _resp[1]]))

        # Bases
        parser = _InverseBasesParser()
        bases, ext = parser.parse(bases_path)
        bases['inverseBasesCoefficients'][0] = bases['inverseBasesCoefficients'][0].reshape(
            bases['nBases'][0], bases['nInverseBasesCoefficients'][0])
        bases['transformationMatrix'][0] = bases['transformationMatrix'][0].reshape(
            bases['nBases'][0], bases['nTransformedBases'][0])

        return cls(dispersion, response, bases)

    def _get_response(self, wavelength):
        """
        Get the response of the mean instrument at a certain wavelength.

        Args:
            wavelength (float): The absolute wavelength.

        Returns:
            float: The response of the mean instrument at the input wavelength.
        """
        tck = interpolate.splrep(
            self.response.get("wavelength"),
            self.response.get("response"),
            s=0)
        return interpolate.splev(wavelength, tck, der=0)

    def _wl_to_pwl(self, wavelength):
        """
        Convert the input absolute wavelength to a pseudo-wavelength.

        Args:
            wavelength (float): Absolute wavelength.

        Returns:
            float: The corresponding pseudo-wavelength value.
        """
        tck = interpolate.splrep(
            self.dispersion.get("wavelength"),
            self.dispersion.get("pseudo-wavelength"),
            s=0)
        return interpolate.splev(wavelength, tck, der=0)


class _InverseBasesParser(GenericParser):
    """
    Parser for the inverse bases used in the external calibration.
    """

    def _parse_csv(self, csv_file):
        """
        Parse the input CSV file and store the result in a pandas DataFrame if it
        contains inverse bases.

        Args:
            csv_file (str): Path to a CSV file.

        Returns:
            DataFrame: Pandas DataFrame populated with the content of the CSV file.
        """
        return super()._parse_csv(
            csv_file,
            array_columns=['inverseBasesCoefficients', 'transformationMatrix'],
            matrix_columns=[])
