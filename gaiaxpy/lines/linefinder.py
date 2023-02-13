"""
linefinder.py
===========================
Module for the line finding.
"""

from configparser import ConfigParser

from gaiaxpy.config.paths import config_path
from gaiaxpy.converter.config import load_config
from gaiaxpy.core.satellite import BANDS, BP_WL, RP_WL
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.lines.herm import HermiteDer
from gaiaxpy.calibrator.externl_instrument_model import ExternalInstrumentModel
from gaiaxpy.spectrum.xp_sampled_spectrum import XpSampledSpectrum

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))
config_file = path.join(config_path, config_parser.get('converter', 'optimised_bases'))
dispersion_file = path.join(config_path, config_parser.get('core', 'dispersion_function'))

def _get_values_continuum_atroots(roots):
    xpss = XpSampledSpectrum()
    return xpss.from_continuous(continuous_spectrum, sampled_basis_functions)
def _get_values_atroots(roots):
    xpss = XpSampledSpectrum()
    return xpss.from_continuous(continuous_spectrum, sampled_basis_functions, truncation=2)
def _get_configuration(config):
   # bp rp?
   # are the bases symetric ie. config[dimesion]==config[transformedSetDimension]???
    """
    Get info from config file.
    
    Args:
        config (DataFrame): The configuration of the set of bases
                loaded into a DataFrame.
    
    Returns:
        (tuple): bases_transformation, n_bases, scale, offset
    """
    if config['transformedSetDimension'] == config['dimension']:
       scale = (config['normalizedRange'].iloc(0)[0][1] - config['normalizedRange'].iloc(0)
       [0][0]) / (config['range'].iloc(0)[0][1] - config['range'].iloc(0)[0][0])
       offset = config['normalizedRange'].iloc(0)[0][0] - config['range'].iloc(0)[0][0] * scale
       bases_transformation = config['transformationMatrix'].iloc(0)[0].reshape(
       int(config['dimension']), int(config['transformedSetDimension']))
       return bases_transformation, int(config['dimension']), scale, offset
    else:
       raise Exception("Transformation matrix is not square. I don't know what to do :(.")
    
def _get_dispersion(dispersion_file):
    wv, dispersion = np.loadtxt(dispersion_file, delimiter = ',')
    bp_dispersion = 
    return bp_dispersion, rp_dispersion

def _wl_to_pwl(wavelength, dispersion):
    # copied and adapted from external_instrument_model.py
    # maybe we can changed it there to visible outside class
        """
        Convert the input absolute wavelength to a pseudo-wavelength.
        Args:
            wavelength (float): Absolute wavelength.
        Returns:
            float: The corresponding pseudo-wavelength value.
        """
        tck = interpolate.splrep(dispersion.get("wavelength"), dispersion.get("pseudo-wavelength"), s=0)
        return interpolate.splev(wavelength, tck, der=0)
def _x_to_pwl(x, scale, offset)
    return (x * scale) + offset
    

  
def linefinder(input_object, sampling=np.linspace(0, 60, 600), lines=None, sourcetype=None, redshift=None, plot=False, 
              username=None, password=None):
  #def linefinder(input_object, sampling=np.linspace(0, 60, 600), lines=None, sourcetype='STAR', redshift=0.):
  # should star type and redshift =0 be a default values
  # no need for sampling argument? we will use default sampling?
    """
    Line finding: get the input interally calobrated man spectra from the continuous represenation to a 
    sampled form. In between it looks for emission and obsorption lines. The lines can be defined by user 
    or chosen from internal library, the source redshift and type can be specified.
    
    Args:
        input_object (object): Path to the file containing the mean spectra as downloaded from the archive in their
            continuous representation, a list of sources ids (string or long), or a pandas DataFrame.
        sampling (ndarray): 1D array containing the desired sampling in pseudo-wavelengths.
        lines (tuple): Tuple containing a list of line wavelengths and names
        source_type (str): Source type: STAR or QSO 
        redshift (list): List of redshifts
        plot (bool): Whether to plot spectrum with lines.
        
    Returns:
        (tuple): tuple with a list of found lines and thier properties
    """
    config_df = load_config(config_file)
    tm, n, scale, offset = _get_configuration(config_df)
    parsed_input_data, extension = InputReader(input_object, convert, username, password)._read()
    config_df = load_config(config_file)
    
    for xp in BANDS:
            instr_model = ExternalInstrumentModel.from_config_csv(_get_file_for_xp(xp, 'dispersion'),
                                                                  _get_file_for_xp(xp, 'response'),
                                                                  _get_file_for_xp(xp, 'bases'))

    
    # coeff from parsedinputdata
    # prep lines
    # run line finder
    # if plot == True: plotting
    
    return lines
    
    
def find(config, n_bases , lines, line_names):
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
  
  
  
