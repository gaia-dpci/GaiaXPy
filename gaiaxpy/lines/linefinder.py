"""
linefinder.py
===========================
Module for the line finding.
"""

from os import path
import numpy as np
import pandas as pd
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

import warnings
warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)


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
        raise Exception('Transformation matrix is not square. I do not know what to do :(.')
    
def _x_to_pwl(x, scale, offset):
    return (x - offset) / scale
    
def _check(source_type, redshift):
    if source_type not in ['qso','star']:
        raise ValueError('Unknown source type. Available source types: `star` and `qso`.')
    if source_type == 'qso' and not isinstance(redshift, list):
        raise ValueError('For QSOs please provide a list of redshifts.')
        
def _check_tr(truncation):
    if not isinstance(truncation, bool): raise ValueError('Argument `truncation` must contain a boolean value.')
    
def _check_pl(plot_spectra, save_plots):
    if not (isinstance(plot_spectra, bool) and isinstance(save_plots, bool)):
        raise ValueError('Arguments `plot_spectra` and `save_plots` must contain a boolean value.')
    if save_plots and not plot_spectra:
        raise ValueError('Argument `plot_spectra` has to be set True if `save_plots` is True.')
    
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
        #try:
            i_line = np.abs(rootspwl - line_pwl).argmin()
            line_root = rootspwl[i_line]
            if abs(line_pwl-line_root) < 1: # allow for 1 pixel difference
            
                line_width_pwl = rootspwl2[rootspwl2>line_root][0] - rootspwl2[rootspwl2<line_root][-1]
                line_width = abs(pwl_to_wl(id, rootspwl2[rootspwl2>line_root][0]).item() - pwl_to_wl(id, rootspwl2[rootspwl2<line_root][-1]).item())
                line_test = np.array([line_root-2.*line_width_pwl, line_root-line_width_pwl, line_root+line_width_pwl, line_root+2.*line_width_pwl])
                
                line_continuum = np.median(flux(pwl_to_wl(id, line_test)))
                line_continuum_pwl = np.median(flux0(line_test))
                
                #line_depth = valroots[i_line] - 0.5*(valroots2[rootspwl2>line_pwl][0]+valroots2[rootspwl2<line_pwl][-1])
                #if name=='H_alpha': line_root+=0.3
                #elif name=='He I_2': line_root+=0.35
                line_wl = pwl_to_wl(id, line_root).item()
                line_flux = flux(line_wl).item()
                line_flux_pwl = flux0(line_root).item()
                line_depth = line_flux-line_continuum
                line_depth_pwl = line_flux_pwl-line_continuum_pwl
                line_sig = abs(line_depth) / fluxerr(line_wl)
                line_sig_pwl = abs(line_depth_pwl) / flux0err(line_root)
                found_lines.append((name,line_pwl,i_line,line_root,line_wl,line_flux,line_depth,line_width,line_sig,line_continuum,line_sig_pwl,line_continuum_pwl,line_width_pwl))
        #except:
        #    pass
          
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
       # try:
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


      #  except:
       #     pass
          
    return found_lines
    
    
def _find_fast(tm, n, n1, scale, offset, id, coeff):
    """
    Extrema (fast) detection: get Hermite coefficients and try to detect all lines/extrema
     
    Args:
        tm (ndarray): Bases transformation matrix
        n (int): Number of bases
        n1 (int): Number of relevant bases
        scale (float): Scale
        offset (float): Offset
        id (str): BP or RP
        coeff (ndarray): Hermite coefficients
    Returns:
        (list): all found extrema (within dispersion function range)
    """
     
    hder = HermiteDer(tm, n, n1, coeff)

    rootspwl = _x_to_pwl(hder.get_roots_firstder(), scale, offset)
    rootspwl2 = _x_to_pwl(hder.get_roots_secondder(), scale, offset)
    
    range = pwl_range(id)
    mask = (rootspwl>min(range))&(rootspwl<max(range))
    rootspwl = rootspwl[mask]
    
    return rootspwl
    
 
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
        redshift (float or list): Default=0 for stars and a list of tuples (source id - redshift) for QSOs
        lines (tuple): Tuple containing a list of line wavelengths [nm] and names
        plot_spectra (bool): Whether to plot spectrum with lines.
        save_plots (bool): Whether to save plots with spectra.
        username (str): Cosmos username, only suggested when input_object is a list or ADQL query.
        password (str): Cosmos password, only suggested when input_object is a list or ADQL query.
        
    Returns:
        (DataFrame): dataframe with arrays of found lines and their properties for each source
    """
    
    _check(source_type, redshift)
    _check_tr(truncation)
    _check_pl(plot_spectra, save_plots)
    
    config_df = load_config(config_file)
    bptm, bpn, bpscale, bpoffset = _get_configuration(get_config(config_df, basis_function_id[BANDS.bp]))
    rptm, rpn, rpscale, rpoffset = _get_configuration(get_config(config_df, basis_function_id[BANDS.rp]))

    # input
    parsed_input_data, extension = InputReader(input_object, linefinder, username, password)._read()
    
    # get converted spectra
    con_spectra, con_sampling = convert(parsed_input_data, truncation=truncation)
    # get calibrated spectra
    cal_spectra, cal_sampling = calibrate(parsed_input_data, truncation=truncation)
    # get calibrated continuum (limit number of bases) -> TO DO: rethink this approach
    temp_input_data = parsed_input_data.copy(deep=True)
    temp_input_data['bp_n_relevant_bases'] = 3
    temp_input_data['rp_n_relevant_bases'] = 3
    cal_continuum, _ = calibrate(temp_input_data, truncation=True)
    # get source_ids
    source_ids = parsed_input_data['source_id']
    # prep redshifts -> match with source_ids
    if source_type == 'qso':
        red_array = np.array(redshift, dtype=[('source_id','i8'),('z','f8')])
        if not np.all(np.isin(source_ids, red_array['source_id'])):
            raise ValueError('Missing redshifts in the list?')
            
    # prep lines
    bplines = Lines(BANDS.bp,source_type,user_lines=user_lines)
    rplines = Lines(BANDS.rp,source_type,user_lines=user_lines)
   
    if source_type == 'star':
        bpline_names, bplines_pwl = bplines.get_lines_pwl()
        rpline_names, rplines_pwl = rplines.get_lines_pwl()

    results = pd.DataFrame(columns=['source_id', 'lines'], index=range(source_ids.size))
    
    for i in np.arange(len(parsed_input_data)):
        
        item = parsed_input_data.iloc[i]
        sid = item['source_id']
        
        # coeff from parsedinputdata
        bpcoeff = item['bp_coefficients']
        rpcoeff = item['rp_coefficients']
        
        if truncation:
            bpreln = item['bp_n_relevant_bases']
            rpreln = item['rp_n_relevant_bases']
        else:
            bpreln = bpn
            rpreln = rpn
       
        # prep lines cont.
        if source_type == 'qso':
            bpline_names, bplines_pwl = bplines.get_lines_pwl(zet=red_array['z'][red_array['source_id']==sid][0])
            rpline_names, rplines_pwl = rplines.get_lines_pwl(zet=red_array['z'][red_array['source_id']==sid][0])
            
        # masks
        m_cal = (cal_spectra['source_id']==sid)
        m_con_bp = (con_spectra['source_id']==sid)&(con_spectra['xp']=='BP')
        m_con_rp = (con_spectra['source_id']==sid)&(con_spectra['xp']=='RP')
    
        # run line finder for BP
        if not pd.isna(item['bp_n_parameters']):
            bp_found_lines = _find(bptm, bpn, bpreln, bpscale, bpoffset, BANDS.bp, bpcoeff, bplines_pwl, bpline_names, _flux_interp(cal_sampling, cal_spectra[m_cal]['flux'].values[0]), _flux_interp(cal_sampling, cal_spectra[m_cal]['flux_error'].values[0]), _flux_interp(con_sampling, con_spectra[m_con_bp]['flux'].values[0]), _flux_interp(con_sampling, con_spectra[m_con_bp]['flux_error'].values[0]))
        else:
            bp_found_lines = []
            
        # run line finder for RP
        rp_found_lines = _find(rptm, rpn, rpreln, rpscale, rpoffset, BANDS.rp, rpcoeff, rplines_pwl, rpline_names, _flux_interp(cal_sampling, cal_spectra[m_cal]['flux'].values[0]), _flux_interp(cal_sampling, cal_spectra[m_cal]['flux_error'].values[0]), _flux_interp(con_sampling, con_spectra[m_con_rp]['flux'].values[0]), _flux_interp(con_sampling, con_spectra[m_con_rp]['flux_error'].values[0]))

        # plotting
        if plot_spectra and not pd.isna(item['bp_n_parameters']):
            plot_spectra_with_lines(sid, con_sampling, con_spectra[m_con_bp]['flux'].values[0],  con_spectra[m_con_rp]['flux'].values[0], cal_sampling, cal_spectra[m_cal]['flux'].values[0], cal_continuum[m_cal]['flux'].values[0], bp_found_lines, rp_found_lines, save_plots)
        elif plot_spectra:
            plot_spectra_with_lines(sid, con_sampling, None,  con_spectra[m_con_rp]['flux'].values[0], cal_sampling, cal_spectra[m_cal]['flux'].values[0], cal_continuum[m_cal]['flux'].values[0], bp_found_lines, rp_found_lines, save_plots)
    
        results.iloc[i] = [sid, _output(bp_found_lines, rp_found_lines)]
       
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
        username (str): Cosmos username, only suggested when input_object is a list or ADQL query.
        password (str): Cosmos password, only suggested when input_object is a list or ADQL query.
        
    Returns:
        (DataFrame): dataframe with arrays of found extrema and their properties for each source
    """
    
    _check_tr(truncation)
    _check_pl(plot_spectra, save_plots)
    
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

    results = pd.DataFrame(columns=['source_id', 'extrema'], index=range(source_ids.size))
    
    for i in np.arange(len(parsed_input_data)):
    
        item = parsed_input_data.iloc[i]
        sid = item['source_id']
        
        # coeff from parsedinputdata
        bpcoeff = item['bp_coefficients']
        rpcoeff = item['rp_coefficients']
        
        if truncation:
            bpreln = item['bp_n_relevant_bases']
            rpreln = item['rp_n_relevant_bases']
        else:
            bpreln = bpn
            rpreln = rpn
    
        # masks
        m_cal = (cal_spectra['source_id']==sid)
        m_con_bp = (con_spectra['source_id']==sid)&(con_spectra['xp']=='BP')
        m_con_rp = (con_spectra['source_id']==sid)&(con_spectra['xp']=='RP')
    
        # run line finder for BP
        if not pd.isna(item['bp_n_parameters']):
            bp_found_lines = _find_all(bptm, bpn, bpreln, bpscale, bpoffset, BANDS.bp, bpcoeff, _flux_interp(cal_sampling, cal_spectra[m_cal]['flux'].values[0]), _flux_interp(cal_sampling, cal_spectra[m_cal]['flux_error'].values[0]), _flux_interp(con_sampling, con_spectra[m_con_bp]['flux'].values[0]), _flux_interp(con_sampling, con_spectra[m_con_bp]['flux_error'].values[0]))
        else:
            bp_found_lines = []
            
        # run line finder for RP
        rp_found_lines = _find_all(rptm, rpn, rpreln, rpscale, rpoffset, BANDS.rp, rpcoeff, _flux_interp(cal_sampling, cal_spectra[m_cal]['flux'].values[0]), _flux_interp(cal_sampling, cal_spectra[m_cal]['flux_error'].values[0]), _flux_interp(con_sampling, con_spectra[m_con_rp]['flux'].values[0]), _flux_interp(con_sampling, con_spectra[m_con_rp]['flux_error'].values[0]))

        # plotting
        if plot_spectra and not pd.isna(item['bp_n_parameters']):
            plot_spectra_with_lines(sid, con_sampling, con_spectra[m_con_bp]['flux'].values[0],  con_spectra[m_con_rp]['flux'].values[0], cal_sampling, cal_spectra[m_cal]['flux'].values[0], cal_continuum[m_cal]['flux'].values[0], bp_found_lines, rp_found_lines, save_plots)
        elif plot_spectra:
            plot_spectra_with_lines(sid, con_sampling, None,  con_spectra[m_con_rp]['flux'].values[0], cal_sampling, cal_spectra[m_cal]['flux'].values[0], cal_continuum[m_cal]['flux'].values[0], bp_found_lines, rp_found_lines, save_plots)
            
            
        results.iloc[i] = [sid, _output(bp_found_lines, rp_found_lines)]
       
    return results
    
    
def fastfinder(input_object, truncation=False, username=None, password=None):
    """
    Line finding: get the input coefficents for interally calibrated mean spectra and look for the extrema. No evalution of spectra in both sampled and continuous forms is performed
    
    Args:
        input_object (object): Path to the file containing the mean spectra as downloaded from the archive in their
            continuous representation, a list of sources ids (string or long), or a pandas DataFrame.
        truncation (bool): Toggle truncation of the set of bases. The level of truncation to be applied is defined by the recommended value in the input files.
        username (str): Cosmos username, only suggested when input_object is a list or ADQL query.
        password (str): Cosmos password, only suggested when input_object is a list or ADQL query.
        
    Returns:
        (DataFrame): dataframe with arrays of found extrema for each source
    """
     
    _check_tr(truncation)

    config_df = load_config(config_file)
    bptm, bpn, bpscale, bpoffset = _get_configuration(get_config(config_df, basis_function_id[BANDS.bp]))
    rptm, rpn, rpscale, rpoffset = _get_configuration(get_config(config_df, basis_function_id[BANDS.rp]))

    # input
    parsed_input_data, extension = InputReader(input_object, linefinder, username, password)._read()
    
    # get source_ids
    source_ids = parsed_input_data['source_id']
    
    results = pd.DataFrame(columns=['source_id', 'extrema_bp', 'extrema_rp'], index=range(source_ids.size))
    
    for i in np.arange(len(parsed_input_data)):
    
        item = parsed_input_data.iloc[i]
        sid = item['source_id']
        
        # coeff from parsedinputdata
        bpcoeff = item['bp_coefficients']
        rpcoeff = item['rp_coefficients']
        
        if truncation:
            bpreln = item['bp_n_relevant_bases']
            rpreln = item['rp_n_relevant_bases']
        else:
            bpreln = bpn
            rpreln = rpn
    
        # run line finder for BP
        if not pd.isna(item['bp_n_parameters']):
            bp_found_lines = _find_fast(bptm, bpn, bpreln, bpscale, bpoffset, BANDS.bp, bpcoeff)
        else:
            bp_found_lines = []
            
        # run line finder for RP
        rp_found_lines = _find_fast(rptm, rpn, rpreln, rpscale, rpoffset, BANDS.rp, rpcoeff)
   
        results.iloc[i] = [sid, bp_found_lines, rp_found_lines]
       
    return results
