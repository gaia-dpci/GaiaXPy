
import numpy as np

from gaiaxpy.lines.linefinder import _wl_to_pwl
from gaiaxpy.core.satellite import BANDS, BP_WL, RP_WL

# local library of lines
_qsoline_names = ['Ly_alpha','C IV','C III]','Mg II','H_beta','H_alpha']
_qsolines = [121.524,154.948,190.8734,279.9117,486.268,656.461]

_starline_names = ['H_beta','H_alpha','He I_1','He I_2','He I_3']
_starlines = [486.268,656.461,447.3,587.7,706.7]



class Lines():
  
  def __init__(self, xp, src_type, dispersion):
    self.xp = xp
    self.src_type = src_type
    self.disp = dispersion

  def get_lines_pwl(self, zet=0., userlines=None): 

    lines = []

    if userlines == None: #get lines from local library
      if self.src_type == 'star':
        inputlines = _starline
        inputlinenames = _starline_names
      elif self.src_type == 'qso':
        inputlines = _qsoline
        inputlinenames = _qsoline_names
    else:
      inputlines = userlines[0]
      inputlinenames = userlines[1]
    
    inputlines = np.array(inputlines)
    inputlinenames = np.array(inputlinenames)
    
    # redshifted lines in wavelength
    inputlines = inputlines * (1. + zet)
    if self.xp == BANDS.bp:
         mask = (inputlines)>BP_WL.low)&(inputlines<BP_WL.high)  # mask outside wavelength range range
         line_pwl = _wl_to_pwl(inputlines[mask], self.disp)
         lines = (np.asarray(inputlinenames)[mask], line_pwl)
    elif self.xp == BANDS.rp:
         mask = (inputlines)>RP_WL.low)&(inputlines<RP_WL.high)  # mask outside wavelength range range
         line_pwl = _wl_to_pwl(inputlines[mask], self.disp)
         lines = (np.asarray(inputlinenames)[mask], line_pwl)
        
    return lines  
