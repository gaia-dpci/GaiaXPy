from os import path

import numpy as np

from gaiaxpy.core.dispersion_function import wl_to_pwl
from gaiaxpy.core.satellite import BANDS, BP_WL, RP_WL
from gaiaxpy.linefinder.utils import _validate_source_type

# local library of lines
_qso_line_names = ['Ly_alpha', 'C IV', 'C III]', 'Mg II', 'H_beta', 'H_alpha']
_qso_lines = [121.524, 154.948, 190.8734, 279.9117, 486.268, 656.461]

_star_line_names = ['H_beta', 'H_alpha', 'He I_1', 'He I_2', 'He I_3']
_star_lines = [486.268, 656.461, 447.3, 587.7, 706.7]


class Lines:
    """
    Create a set of lines.
    """

    def __init__(self, xp, src_type, user_lines=None):
        """
        Initialise line lists.
        
        Args:
            xp (str): BP or RP.
            src_type (str): Type of sources (star or quasars).
            user_lines (list/str): List of lines defined by user.
        """

        self.xp = xp
        self.src_type = _validate_source_type(src_type)

        if user_lines is None:  # Get lines from local library
            if self.src_type == 'star':
                input_lines = _star_lines
                input_line_names = _star_line_names
            elif self.src_type == 'qso':
                input_lines = _qso_lines
                input_line_names = _qso_line_names
            else:
                raise ValueError("Unknown source type. Valid source types are: 'qso' and 'star'.")
        else:
            if isinstance(user_lines, list):  # Get lines from a list provided by user
                input_lines = user_lines[0]
                input_line_names = user_lines[1]
            elif path.isfile(user_lines):  # Get lines from a file provided by user
                input_lines, input_line_names = np.loadtxt(user_lines, unpack=True, dtype='f8,U12')
            else:
                raise ValueError('Input is not corresponding to a list of lines or an existing file.')

        self.in_lines = np.array(input_lines)
        self.in_line_names = np.array(input_line_names)

    def get_lines_pwl(self, zet=0.):
        """
        Calculate pseudo-wavelength of lines.
        
        Args:
            zet (float): Redshift of source. Default = 0. (for stars).
    
        Returns:
            list: List of (redshifted) lines in pseudo-wavelengths with their names.
        """
        lines = []
        # Redshifted lines in wavelength
        in_lines_red = self.in_lines * (1. + zet)

        if self.xp == BANDS.bp:
            mask = (in_lines_red > BP_WL.low) & (in_lines_red < BP_WL.high)  # Mask outside wavelength range range
            line_pwl = wl_to_pwl(self.xp, in_lines_red[mask])
            lines = (np.asarray(self.in_line_names)[mask], line_pwl)
        elif self.xp == BANDS.rp:
            mask = (in_lines_red > RP_WL.low) & (in_lines_red < RP_WL.high)  # Mask outside wavelength range range
            line_pwl = wl_to_pwl(self.xp, in_lines_red[mask])
            lines = (np.asarray(self.in_line_names)[mask], line_pwl)

        return lines

    def get_units(cls):
        return {'wavelength_nm': 'nm', 'line_flux': 'W nm^-1 m^-2', 'depth': 'W nm^-1 m^-2', 'width': 'nm'}


class Extrema:
    """
    Mock object for output units.
    """

    def __init__(self):
        pass

    def get_units(cls):
        return {}
