import numpy as np

from gaiaxpy.core.dispersion_function import wl_to_pwl, pwl_to_wl
from gaiaxpy.core.satellite import BANDS, BP_WL, RP_WL

# local library of lines
_qsoline_names = ['Ly_alpha','C IV','C III]','Mg II','H_beta','H_alpha']
_qsolines = [121.524,154.948,190.8734,279.9117,486.268,656.461]

_starline_names = ['H_beta','H_alpha','He I_1','He I_2','He I_3']
_starlines = [486.268,656.461,447.3,587.7,706.7]


class Lines():
    """
    Create a set of lines.
    """
    
    def __init__(self, xp, src_type, user_lines=None):
        """
        Initialise line lists.
        
        Args:
            xp (str): BP or RP.
            src_type (str): Type of sources (star or quasars).
            user_lines (list): List of lines defined by user.
        """

        self.xp = xp
        self.src_type = src_type
    
        if user_lines == None: #get lines from local library
            if self.src_type == 'star':
                inputlines = _starlines
                inputlinenames = _starline_names
            elif self.src_type == 'qso':
                inputlines = _qsolines
                inputlinenames = _qsoline_names
        else:
            inputlines = user_lines[0]
            inputlinenames = user_lines[1]
    
        self.inlines = np.array(inputlines)
        self.inlinenames = np.array(inputlinenames)

    def get_lines_pwl(self, zet=0.):
        """
        Calculate pseudo-wavelength of lines.
        
        Args:
            zet (float): Redshift of source. Default = 0. (for stars).
    
        Returns:
            list: Lisst of (redshifted) lines in pseudo-wavelengths with their names.
        """

        lines = []
    
        # redshifted lines in wavelength
        inlinesred = self.inlines * (1. + zet)
   
        if self.xp == BANDS.bp:
            mask = (inlinesred>BP_WL.low)&(inlinesred<BP_WL.high)  # mask outside wavelength range range
            line_pwl = wl_to_pwl(self.xp, inlinesred[mask])
            lines = (np.asarray(self.inlinenames)[mask], line_pwl)
        elif self.xp == BANDS.rp:
            mask = (inlinesred>RP_WL.low)&(inlinesred<RP_WL.high)  # mask outside wavelength range range
            line_pwl = wl_to_pwl(self.xp, inlinesred[mask])
            lines = (np.asarray(self.inlinenames)[mask], line_pwl)
        
        return lines
