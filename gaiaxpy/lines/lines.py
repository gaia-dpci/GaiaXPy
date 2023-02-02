
import numpy as np

from gaiaxpy.config.paths import config_path

# local library of lines
_qsoline_names = ['Ly_alpha','C IV','C III]','Mg II','H_beta','H_alpha']
_qsolines = [121.524,154.948,190.8734,279.9117,486.268,656.461]

_starline_names = ['H_beta','H_alpha','He I_1','He I_2','He I_3']
_starlines = [486.268,656.461,447.3,587.7,706.7]


_rp_dispersion = np.loadtxt(config_path + '/rpC03_v142r_dispersion.csv', delimiter = ',')
_rp_wvl = _rp_dispersion[0]
_rp_pwl = _rp_dispersion[1]

_bp_dispersion = np.loadtxt(config_path + '/bpC03_v375wi_dispersion.csv', delimiter = ',')
_bp_wvl = _bp_dispersion[0]
_bp_pwl = _bp_dispersion[1]

class Lines():
  
  def __init__(self, src_type, xp):
    self.src_type = src_type
    self.xp = xp

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
      

      
      # redshifted lines in wavelength
    inputlines = inputlines * (1. + zet)
    if self.xp == 'BP':
         line_pwl = np.interp(inputlines[(_bp_wvl[0]<inputlines)&(inputlines<_bp_wvl[-1])], _bp_wvl, _bp_pwl)
         lines = (np.asarray(inputlinenames)[(_bp_wvl[0]<inputlines)&(inputlines<_bp_wvl[-1])], line_pwl)
    elif self.xp == 'RP':
         line_pwl = np.interp(inputlines[(_rp_wvl[0]<inputlines)&(inputlines<_rp_wvl[-1])], _rp_wvl, _rp_pwl)
         lines = (np.asarray(inputlinenames)[(_rp_wvl[0]<inputlines)&(inputlines<_rp_wvl[-1])], line_pwl)

    return lines  
