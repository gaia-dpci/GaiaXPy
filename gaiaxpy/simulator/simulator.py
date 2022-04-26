"""
simulator.py
====================================
Module for the simulator functionality.
"""

import numpy as np
import pandas as pd
from configparser import ConfigParser
from os import path
from gaiaxpy import converter
from gaiaxpy.core import nature, _get_spectra_type, _progress_tracker, \
                         _validate_arguments, _validate_pwl_sampling
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.config import config_path
from gaiaxpy.input_reader import InputReader
from gaiaxpy.output import ContinuousSpectraData, SampledSpectraData
from gaiaxpy.spectrum import XpContinuousSpectrum, XpSampledSpectrum
from .config import load_config
from .rebin import _rebin
from scipy.interpolate import interp1d, splrep, splev
from .xp_instrument_model import XpInstrumentModel

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))
model_config_file = path.join(config_path, config_parser.get('simulator', 'model'))
bases_config_file = path.join(config_path, config_parser.get('converter', 'optimised_bases'))

def simulate_sampled(
        sed,
        sampling=np.linspace(0, 60, 600),
        save_path='.',
        output_file='output_spectra',
        output_format=None,
        save_file=True):
    """
    Simulation utility: converts the input SED to the internal Gaia
    BP/RP system.

    Args:
        sed (str): Path to the file containing the SED.
        sampling (ndarray): 1D array containing the desired sampling in
            pseudo-wavelengths.
        save_path (str): Path where to save the output data.
        output_file (str): Name of the output file.
        output_format (str): Format to be used for the output file. If no format
            is given, then the output file will be in the same format as the
            input file.
        save_file (bool): Whether to save the output in a file. If false, output_format
            and output_file are ignored.

    Returns:
        (tuple): tuple containing:
            DataFrame: The values for all sampled spectra.
            ndarray: The sampling used to simulate the input spectra (user-provided or default).

    Raises:
        ValueError: If the sampling is out of the expected boundaries.
    """
    _validate_pwl_sampling(sampling)
    _validate_arguments(simulate_sampled.__defaults__[2], output_file, save_file)
    model_dict = load_config(model_config_file)
    parsed_seds, extension = InputReader(sed, simulate_sampled)._read()

    spectra_list = _simulate_sampled_spectra(parsed_seds, model_dict, sampling)

    spectra_df = pd.DataFrame.from_records([spectrum._spectrum_to_dict() \
                 for spectrum in spectra_list])
    spectra_type = _get_spectra_type(spectra_list)
    spectra_df.attrs['data_type'] = spectra_type
    positions = spectra_list[0]._get_positions()
    output_data = SampledSpectraData(spectra_df, positions)
    output_data.save(save_file, save_path, output_file, output_format, extension)
    # Return dataframe with data and positions
    return spectra_df, positions

def _simulate_sampled_spectra(seds, models, sampling):
    spectra_list = []
    n_rows = len(seds)

    @_progress_tracker
    def _simulate_sampled_spectrum(sed_id, sed_flux, sed_error, band, model, sampling, *args):
        al = model.get_al()
        f = model.get_flux(sed_flux)
        e = model.get_flux_error(sed_flux, sed_error)
        # Interpolate on the user-defined grid
        #f_interpolator = interp1d(al, f, kind='cubic')
        #e_interpolator = interp1d(al, e, kind='cubic')
        #f_interpolated = [f_interpolator(u) for u in sampling]
        #e_interpolated = [e_interpolator(u) for u in sampling]
        f_spl = splrep(al, f, k=2)
        e_spl = splrep(al, e, k=2)
        f_interpolated = splev(sampling, f_spl)
        e_interpolated = splev(sampling, e_spl)
        sampled = XpSampledSpectrum.from_sampled(sed_id, band,
                                              sampling,
                                              f_interpolated,
                                              e_interpolated)
        spectra_list.append(sampled)

    for index, row in seds.iterrows():
        for band in BANDS:
            model: XpInstrumentModel = models[band]
            sed_flux, sed_error = _rebin_and_convert_sed(row, model.get_wl())
            _simulate_sampled_spectrum(row['source_id'], sed_flux, sed_error, band, model, sampling, index, n_rows)

    return spectra_list

def _rebin_and_convert_sed(sed, wl_grid):
    keys = ['wl', 'flux', 'flux_error']
    variable_names = ['wl', 'fl', 'er']
    variables_dict = {}
    for key, variable_name in zip(keys, variable_names):
        try:
            variables_dict[variable_name] = sed[key]
        except KeyError:
            raise KeyError(f'Required column {key} is not present in input data.')
    wl = variables_dict['wl']
    fl = variables_dict['fl']
    er = variables_dict['er']
    # Rebin
    fl_el = [fl, er]
    fl_rebinned, er_rebinned = _rebin(wl, fl_el, wl_grid)
    fl_phot_per_sec = _to_phot_per_sec(wl_grid, fl_rebinned)
    er_phot_per_sec = _to_phot_per_sec(wl_grid, er_rebinned)
    return fl_phot_per_sec, er_phot_per_sec

def _continuous_spectra_to_df(data):
    spectra_bp_df = pd.DataFrame.from_records(
                    [spectrum[BANDS.bp]._spectrum_to_dict() for spectrum in data])
    spectra_rp_df = pd.DataFrame.from_records(
                    [spectrum[BANDS.rp]._spectrum_to_dict() for spectrum in data])
    spectra_df = spectra_bp_df.merge(spectra_rp_df, on='source_id', how='outer')
    for col in spectra_df.columns:
        if 'xp' in col:
            spectra_df = spectra_df.drop(col, axis=1)
        else:
            if '_x' in col:
                col_new = col.replace('_x', '')
                col_new = f'{BANDS.bp}_' + col_new
                spectra_df = spectra_df.rename(columns={col: col_new})
            if '_y' in col:
                col_new = col.replace('_y', '')
                col_new = f'{BANDS.rp}_' + col_new
                spectra_df = spectra_df.rename(columns={col: col_new})
    return spectra_df

def simulate_continuous(
        sed,
        save_path='.',
        output_file='output_spectra',
        output_format=None,
        save_file=True):
    """
    Simulation utility: converts the input SED to the internal Gaia
    BP/RP system.

    Args:
        sed (str): Path to the file containing the SED.
        save_path (str): Path where to save the output data.
        output_file (str): Name of the output file.
        output_format (str): Format to be used for the output file. If no format
            is given, then the output file will be in the same format as the
            input file.
        save_file (bool): Whether to save the output in a file. If false, output_format
            and output_file are ignored.

    Returns:
        DataFrame: a DataFrame of all continuous spectra.

    Raises:
        ValueError: If the sampling is out of the expected boundaries.
    """
    _validate_arguments(simulate_continuous.__defaults__[1], output_file, save_file)
    model_dict = load_config(model_config_file)
    parsed_seds, extension = InputReader(sed, simulate_continuous)._read()
    continuous_spectra_list = _simulate_continuous_spectra(parsed_seds, model_dict)
    spectra_df = _continuous_spectra_to_df(continuous_spectra_list)
    output_data = ContinuousSpectraData(spectra_df)
    output_data.save(save_file, save_path, output_file, output_format, extension)
    return spectra_df

def _simulate_continuous_spectra(parsed_seds, model_dict):
    """
    Internal wrapper function. Allows _create_continuous_spectrum to use the
    generic progress tracker.
    """
    spectra_list = []
    nrows = len(parsed_seds)
    @_progress_tracker
    def create_continuous_spectrum(row, *args):
        out = dict()
        for band in BANDS:
            model: XpInstrumentModel = model_dict[band]
            out[band] = _create_continuous_spectrum(row, band, model)
        spectra_list.append(out)
    for index, row in parsed_seds.iterrows():
        create_continuous_spectrum(row, index, nrows)
    return spectra_list

def _create_continuous_spectrum(row, band, model):
    # The following sets the standard deviation to 1.0. This is wrong. I think
    # the standard deviation is not needed any more in the continuous spectrum.
    # To be confirmed.
    keys = ['wl', 'flux', 'flux_error']
    variable_names = ['wl', 'fl', 'el']
    variables_dict = {}
    for key, variable_name in zip(keys, variable_names):
        try:
            variables_dict[variable_name] = row[key]
        except KeyError:
            raise KeyError(f'Required column {key} is not present in input data.')
    wl = variables_dict['wl']
    fl = variables_dict['fl']
    el = variables_dict['el']
    wl_grid = model.get_wl()
    # Rebin
    fl_el = [fl, el]
    fl_rebinned, el_rebinned = _rebin(wl, fl_el, wl_grid)
    fl_phot_per_sec = _to_phot_per_sec(wl_grid, fl_rebinned)
    el_phot_per_sec = _to_phot_per_sec(wl_grid, el_rebinned)
    return XpContinuousSpectrum(row['source_id'], band, model.get_coefficients(fl_phot_per_sec),
                                model.get_covariance(fl_phot_per_sec, el_phot_per_sec), 1.0)

def _to_phot_per_sec(wl, sed):
    """
    Convert input SED and wavelength in nanometers to photons per second.
    """
    hc = 1.e9 * nature.C * nature.PLANCK
    return sed * wl / hc
