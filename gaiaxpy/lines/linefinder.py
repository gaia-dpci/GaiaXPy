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
from gaiaxpy.core.dispersion_function import wl_to_pwl, pwl_to_wl, pwl_range
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
    
def _check(source_type, redshift):
    if source_type not in ['qso','star']:
        raise ValueError('Unknown source type. Available source types: "star" and "qso".')
    if source_type == 'qso' and not isinstance(redshift, list):
        raise ValueError('For QSOs please provide a list of redshifts.')
    
def _flux_interp (wl,flux):
    return interpolate.interp1d(wl,flux,fill_value='extrapolate')
    
def _find(tm, n, n1, scale, offset, id, coeff, lines, line_names, flux, fluxerr, flux0, flux0err):
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
        flux (ndarray): Calibrated flux [W/nm/m2]
        fluxerr (ndarray): Error of calibrated flux
        flux0 (ndarray): Flux in pwl [e/s]
        flux0err (ndarray): Error of flux
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
            
                line_width_pwl = rootspwl2[rootspwl2>line_root][0] - rootspwl2[rootspwl2<line_root][-1]
                line_width = abs(pwl_to_wl(id, rootspwl2[rootspwl2>line_root][0]).item() - pwl_to_wl(id, rootspwl2[rootspwl2<line_root][-1]).item())
                line_test = np.array([line_root-2.*line_width_pwl, line_root-line_width_pwl, line_root+line_width_pwl, line_root+2.*line_width_pwl])
                
                line_continuum = np.median(flux(pwl_to_wl(id, line_test)))
                line_continuum_pwl = np.median(flux0(line_test))
                
                line_wl = pwl_to_wl(id, line_root).item()
                line_flux = flux(line_wl).item()
                line_flux_pwl = flux0(line_root).item()
                line_depth = line_flux-line_continuum
                line_depth_pwl = line_flux_pwl-line_continuum_pwl
                line_sig = abs(line_depth) / fluxerr(line_wl)
                line_sig_pwl = abs(line_depth_pwl) / flux0err(line_root)
                found_lines.append((name,line_pwl,i_line,line_root,line_wl,line_flux,line_depth,line_width,line_sig,line_continuum,line_sig_pwl,line_continuum_pwl,line_width_pwl))
        except:
            pass
          
    return found_lines
    
def _find_all(tm, n, n1, scale, offset, id, coeff, flux, fluxerr, flux0, flux0err):
    """
    Extrema detection: get Hermite coefficients and try to detect all lines/extrema
     
    Args:
        tm (ndarray): Bases transformation matrix
        n (int): Number of bases
        n1 (int): Number of relevant bases
        scale (float): Scale
        offset (float): Offset
        id (str): BP or RP
        coeff (ndarray): Hermite coefficients
        flux (ndarray): Calibrated flux
        fluxerr (ndarray): Error of calibrated flux
        flux0 (ndarray): Flux in pwl [e/s]
        flux0err (ndarray): Error of flux
    Returns:
        (list): all found extrema (within dispersion function range) with their properties
    """
     
    hder = HermiteDer(tm, n, n1, coeff)

    rootspwl = _x_to_pwl(hder.get_roots_firstder(), scale, offset)
    rootspwl2 = _x_to_pwl(hder.get_roots_secondder(), scale, offset)
    
    range = pwl_range(id)
    mask = (rootspwl>min(range))&(rootspwl<max(range))
    rootspwl = rootspwl[mask]
    
    found_lines = []

    for i_line,line_root in enumerate(rootspwl):
        try:
            line_flux = flux(pwl_to_wl(id, line_root).item())
            line_width_pwl = rootspwl2[rootspwl2>line_root][0]-rootspwl2[rootspwl2<line_root][-1]
            line_width = abs(pwl_to_wl(id, rootspwl2[rootspwl2>line_root][0]).item() - pwl_to_wl(id, rootspwl2[rootspwl2<line_root][-1]).item())
            line_test = np.array([line_root-2.*line_width_pwl, line_root-line_width_pwl, line_root+line_width_pwl, line_root+2.*line_width_pwl])
            line_continuum = np.median(flux(pwl_to_wl(id, line_test)))
            line_continuum_pwl = np.median(flux0(line_test))
            line_depth = line_flux-line_continuum
            line_wl = pwl_to_wl(id, line_root).item()
            line_sig = abs(line_depth) / fluxerr(line_wl)
            line_flux_pwl = flux0(line_root).item()
            line_depth_pwl = line_flux_pwl-line_continuum_pwl
            line_sig_pwl = abs(line_depth_pwl) / flux0err(line_root)
            name = id+'_'+str(int(line_wl))
            found_lines.append((name,line_root,i_line,line_root,line_wl,line_flux,line_depth,line_width,line_sig,line_continuum,line_sig_pwl,line_continuum_pwl,line_width_pwl))

        except:
            pass
          
    return found_lines
 
def _output (bp_found_lines,rp_found_lines):
    """
    Just create a nice output.
    """
    found_lines = []
    for line in bp_found_lines:
        out = (line[0],line[4],line[5],line[6],line[7],line[8],line[10])
        found_lines.append(out)
    for line in rp_found_lines:
        out = (line[0],line[4],line[5],line[6],line[7],line[8],line[10])
        found_lines.append(out)
    dtype = [('line_name','U12'),('wavelength_nm','f8'),('flux','f8'),('depth','f8'),('width','f8'),('significance','f8'),('sig_pwl','f8')]
    found_lines = np.array(found_lines, dtype=dtype)
    found_lines = np.sort(found_lines, order='wavelength_nm')
    return found_lines
    
  
def linefinder(input_object, truncation=False, source_type='star', redshift=0., user_lines=None, plot_spectra=False, save_plots=False, username=None, password=None):
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
        save_plots (bool): Whether to save plots with spectra.
        
    Returns:
        (list): list with an array of found lines and their properties for each source
    """
    
    _check(source_type, redshift)
    
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
    source_ids = parsed_input_data['source_id']
    
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
        bp_found_lines = _find(bptm, bpn, bpreln, bpscale, bpoffset, BANDS.bp, bpcoeff, bplines_pwl, bpline_names, _flux_interp(cal_sampling, cal_spectra.iloc[i]['flux']), _flux_interp(cal_sampling, cal_spectra.iloc[i]['flux_error']), _flux_interp(con_sampling, con_spectra.iloc[2*i]['flux']), _flux_interp(con_sampling, con_spectra.iloc[2*i]['flux_error']))
        # run line finder for RP
        rp_found_lines = _find(rptm, rpn, rpreln, rpscale, rpoffset, BANDS.rp, rpcoeff, rplines_pwl, rpline_names, _flux_interp(cal_sampling, cal_spectra.iloc[i]['flux']), _flux_interp(cal_sampling, cal_spectra.iloc[i]['flux_error']), _flux_interp(con_sampling, con_spectra.iloc[2*i+1]['flux']), _flux_interp(con_sampling, con_spectra.iloc[2*i+1]['flux_error']))

        # plotting
        if plot_spectra:
            plot_spectra_with_lines(source_ids[i], con_sampling, con_spectra.iloc[2*i]['flux'],  con_spectra.iloc[2*i+1]['flux'], cal_sampling, cal_spectra.iloc[i]['flux'], cal_continuum.iloc[i]['flux'], bp_found_lines, rp_found_lines, save_plots)
            
    
        results.append((source_ids[i], _output(bp_found_lines, rp_found_lines)))
       
    return results


def extremafinder(input_object, truncation=False, plot_spectra=False, save_plots=False, username=None, password=None):
    """
    Line finding: get the input interally calibrated mean spectra from the continuous represenation to a
    sampled form. In between it looks for all lines (=extrema in spectra).
    
    Args:
        input_object (object): Path to the file containing the mean spectra as downloaded from the archive in their
            continuous representation, a list of sources ids (string or long), or a pandas DataFrame.
        truncation (bool): Toggle truncation of the set of bases. The level of truncation to be applied is defined by the recommended value in the input files.
        plot_spectra (bool): Whether to plot spectrum with lines.
        save_plots (bool): Whether to save plots with spectra.
        
    Returns:
        (list): list with an array of found lines and their properties for each source
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
    source_ids = parsed_input_data['source_id']
    


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
       
    
    
        # run line finder for BP
        bp_found_lines = _find_all(bptm, bpn, bpreln, bpscale, bpoffset, BANDS.bp, bpcoeff, _flux_interp(cal_sampling, cal_spectra.iloc[i]['flux']), _flux_interp(cal_sampling, cal_spectra.iloc[i]['flux_error']), _flux_interp(con_sampling, con_spectra.iloc[2*i]['flux']), _flux_interp(con_sampling, con_spectra.iloc[2*i]['flux_error']))
        # run line finder for RP
        rp_found_lines = _find_all(rptm, rpn, rpreln, rpscale, rpoffset, BANDS.rp, rpcoeff, _flux_interp(cal_sampling, cal_spectra.iloc[i]['flux']), _flux_interp(cal_sampling, cal_spectra.iloc[i]['flux_error']), _flux_interp(con_sampling, con_spectra.iloc[2*i+1]['flux']), _flux_interp(con_sampling, con_spectra.iloc[2*i+1]['flux_error']))

        # plotting
        if plot_spectra:
            plot_spectra_with_lines(source_ids[i], con_sampling, con_spectra.iloc[2*i]['flux'],  con_spectra.iloc[2*i+1]['flux'], cal_sampling, cal_spectra.iloc[i]['flux'], cal_continuum.iloc[i]['flux'], bp_found_lines, rp_found_lines, save_plots)
            
    
        results.append((source_ids[i], _output(bp_found_lines, rp_found_lines)))
       
    return results
