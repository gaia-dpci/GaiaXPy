"""
linefinder.py
===========================
Module for the line finding.
"""

from os import path
import numpy as np
from scipy import interpolate
from configparser import ConfigParser

from gaiaxpy.calibrator.calibrator import calibrate
from gaiaxpy.config.paths import config_path
from gaiaxpy.converter.config import load_config, get_config
from gaiaxpy.converter.converter import convert
from gaiaxpy.core.dispersion_function import wl_to_pwl, pwl_to_wl
from gaiaxpy.core.satellite import BANDS, BP_WL, RP_WL
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.lines.herm import HermiteDer
from gaiaxpy.lines.lines import Lines
from gaiaxpy.lines.plotter import plot_spectra_with_lines


config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))
config_file = path.join(config_path, config_parser.get('converter', 'optimised_bases'))


basis_function_id = {BANDS.bp: 56, BANDS.rp: 57}


def _get_configuration(config):
    """
    Get info from config file.
    
    Args:
        config (DataFrame): The configuration of the set of bases
                loaded into a DataFrame.
    
    Returns:
        (tuple): bases_transformation, n_bases, scale, offset
    """
    if int(config['transformedSetDimension']) == int(config['dimension']):
        scale = (config['normalizedRange'].iloc(0)[0][1] - config['normalizedRange'].iloc(0)
        [0][0]) / (config['range'].iloc(0)[0][1] - config['range'].iloc(0)[0][0])
        offset = config['normalizedRange'].iloc(0)[0][0] - config['range'].iloc(0)[0][0] * scale
        bases_transformation = config['transformationMatrix'].iloc(0)[0].reshape(
        int(config['dimension']), int(config['transformedSetDimension']))
        return bases_transformation, int(config['dimension']), scale, offset
    else:
        raise Exception("Transformation matrix is not square. I don't know what to do :(.")
    
def _x_to_pwl(x, scale, offset):    
    return (x - offset) / scale
  
def linefinder(input_object, truncation=False, source_type='star', redshift=0., user_lines=None, plot_spectra=False, username=None, password=None):
    """
    Line finding: get the input interally calibrated mean spectra from the continuous represenation to a
    sampled form. In between it looks for emission and absorption lines. The lines can be defined by user
    or chosen from internal library, the source redshift and type can be specified.
    
    Args:
        input_object (object): Path to the file containing the mean spectra as downloaded from the archive in their
            continuous representation, a list of sources ids (string or long), or a pandas DataFrame.
        truncation (bool): Toggle truncation of the set of bases. The level of truncation to be applied is defined by the recommended value in the input files.
        source_type (str): Source type: 'star' or 'qso'
        redshift (float or list): Default=0 for stars or a list of redshifts for QSOs
        lines (tuple): Tuple containing a list of line wavelengths [nm] and names
        plot_spectra (bool): Whether to plot spectrum with lines.
        
    Returns:
        (list): list with a list of found lines and their properties for each source
    """
    
    config_df = load_config(config_file)
    bptm, bpn, bpscale, bpoffset = _get_configuration(get_config(config_df, basis_function_id[BANDS.bp]))
    rptm, rpn, rpscale, rpoffset = _get_configuration(get_config(config_df, basis_function_id[BANDS.rp]))

    # input
    parsed_input_data, extension = InputReader(input_object, linefinder, username, password)._read()
    
    # get converted spectra
    con_spectra, con_sampling = convert(parsed_input_data, truncation=truncation)
    # get calibrated spectra
    cal_spectra, cal_sampling = calibrate(parsed_input_data, truncation=truncation)
    # get calibrated continuum (limit number of bases)
    temp_input_data = parsed_input_data.copy(deep=True)
    temp_input_data['bp_n_relevant_bases'] = 3
    temp_input_data['rp_n_relevant_bases'] = 3
    cal_continuum, _ = calibrate(temp_input_data, truncation=True)
    # get source_ids
    source_ids = np.unique(con_spectra['source_id'])
    
    # prep lines
    bplines = Lines(BANDS.bp,source_type,user_lines=user_lines)
    rplines = Lines(BANDS.rp,source_type,user_lines=user_lines)
   
    if source_type == 'star':
        bpline_names, bplines_pwl = bplines.get_lines_pwl()
        rpline_names, rplines_pwl = rplines.get_lines_pwl()
    
    results = []
    for i in np.arange(len(parsed_input_data)):
        # coeff from parsedinputdata
        bpcoeff = parsed_input_data.iloc[i]['bp_coefficients']
        rpcoeff = parsed_input_data.iloc[i]['rp_coefficients']
                
        if truncation:
            bpreln = parsed_input_data.iloc[i]['bp_n_relevant_bases']
            rpreln = parsed_input_data.iloc[i]['rp_n_relevant_bases']
        else:
            bpreln = bpn
            rpreln = rpn
       
        # prep lines
        if source_type == 'qso':
            bpline_names, bplines_pwl = bplines.get_lines_pwl(zet=redshift[i])
            rpline_names, rplines_pwl = rplines.get_lines_pwl(zet=redshift[i])
    
        # run line finder for BP
        bp_found_lines = find(bptm, bpn, bpreln, bpscale, bpoffset, BANDS.bp, bpcoeff, bplines_pwl, bpline_names, _flux_interp(cal_sampling, cal_spectra.iloc[i]['flux']))
        # run line finder for RP
        rp_found_lines = find(rptm, rpn, rpreln, rpscale, rpoffset, BANDS.rp, rpcoeff, rplines_pwl, rpline_names, _flux_interp(cal_sampling, cal_spectra.iloc[i]['flux']))

        # plotting
        if plot_spectra:
            plot_spectra_with_lines(source_ids[i], con_sampling, con_spectra.iloc[2*i]['flux'],  con_spectra.iloc[2*i+1]['flux'], cal_sampling, cal_spectra.iloc[i]['flux'], cal_continuum.iloc[i]['flux'], bp_found_lines, rp_found_lines)

    
        results.append((source_ids[i], bp_found_lines, rp_found_lines))
       
    return results
    
def _flux_interp (wl,flux):
    return interpolate.interp1d(wl,flux)
    
def find(tm, n, n1, scale, offset, id, coeff, lines, line_names, flux):
    """
    Line detection: get Hermite coefficients and try to detect lines from the list
     
    Args:
        tm (ndarray): Bases transformation matrix
        n (int): Number of bases
        n1 (int): Number of relevant bases
        scale (float): Scale
        offset (float): Offset
        id (str): BP or RP
        coeff (ndarray): Hermite coefficients
        lines (list of floats): List of lines to detected [in pwl]
        line_names (list of str): List of line names
     
    Returns:
        (list): found lines with their properties
    """
     
    hder = HermiteDer(tm, n, n1, coeff)

    rootspwl = _x_to_pwl(hder.get_roots_firstder(), scale, offset)
    rootspwl2 = _x_to_pwl(hder.get_roots_secondder(), scale, offset)

    found_lines = []
    for line_pwl,name in zip(lines,line_names):
        try:
            i_line = np.abs(rootspwl - line_pwl).argmin()
            line_root = rootspwl[i_line]
            if abs(line_pwl-line_root) < 1: # allow for 1 pixel difference
                line_flux = flux(pwl_to_wl(id, line_root).item())
                line_depth = 0.#valroots[i_line]-valconroots[i_line]
            #line_depth = valroots[i_line] - 0.5*(valroots2[rootspwl2>line_pwl][0]+valroots2[rootspwl2<line_pwl][-1])
                line_width = rootspwl2[rootspwl2>line_pwl][0]-rootspwl2[rootspwl2<line_pwl][-1]
                found_lines.append((name,line_pwl,i_line,line_root,pwl_to_wl(id, line_root).item(),line_flux,line_depth,line_width))
        except:
            pass
          
    return found_lines
