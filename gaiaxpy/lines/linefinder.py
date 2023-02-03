

from gaiaxpy.lines.herm import HermiteDer


def _get_values_continuum_atroots(roots):
  return None
def _get_values_atroots(roots):
  return roots

def linefinder(config, n_bases , lines, line_names):
     # return line `depth` and `width`  
     # `depth` - difference between flux value at extremum and average value of two nearby inflexion points
     # `width` - distance between two nearby inflexion points
    
     hder = HermiteDer(config, coeff)
    
     found_lines = []
     rootspwl = hder.get_roots_firstder()
     rootspwl2 = hder.get_roots_secondder()
     valroots = _get_values_atroots(rootspwl)
     valroots2 = _get_values_atroots(rootspwl2)
     valconroots = _get_values_continuum_atroots(rootspwl) 

     for line_pwl,name in zip(lines,line_names):
        try:
          i_line = np.abs(rootspwl - line_pwl).argmin()
          line_root = rootspwl[i_line]
          if abs(line_pwl-line_root) < 1: # allow for 1 pixel difference 
            line_flux = valroots[i_line]
            #line_depth = valroots[i_line]-valconroots[i_line]
            line_depth = valroots[i_line] - 0.5*(valroots2[rootspwl2>line_pwl][0]+valroots2[rootspwl2<line_pwl][-1])
            line_width = rootspwl2[rootspwl2>line_pwl][0]-rootspwl2[rootspwl2<line_pwl][-1]
            found_lines.append((name,line_pwl,i_line,line_root,line_flux,line_depth,line_width))
        except:
          pass
          
     return found_lines 
