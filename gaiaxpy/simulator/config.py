"""
config.py
====================================
Module for handling the simulator configuration files.
"""

import numpy as np
import pandas as pd
from ast import literal_eval
from configparser import ConfigParser
from os.path import join
from gaiaxpy.config import config_path
from .xp_instrument_model import XpInstrumentModel
from gaiaxpy.core.satellite import BANDS

config_parser = ConfigParser()
config_parser.read(join(config_path, 'config.ini'))

def load_config(path):
    """
    Load the configuration for the simulator functionality.

    Args:
        path (str): Path to the configuration file.

    Returns:
        Dict: a dictionary containing one model for BP and one for RP.
    """
    return _load_model_from_hdf(path)

def get_file(path, bp_model, rp_model):
    """
    Get the file path corresponding to the given label and key.

    Args:
        bp_model (str): BP instrument model code.
        rp_model (str): RP instrument model code.

    Returns:
        str: File path.
    """
    generic_file_name = f"{path}".replace('model', f'{bp_model}{rp_model}')
    return generic_file_name

def _load_model_from_hdf(
        path,
        bp_model='v375wi',
        rp_model='v142r'):
    """
    Load the MIOG-lite model for each band.

    Args:
        bp_model (str): BP instrument model code.
        rp_model (str): RP instrument model code.

    Returns:
        dict: A dictionary containing the XpInstrumentModel table with one entry for BP and one for RP.
    """
    file_name = get_file(path, bp_model, rp_model)
    # Get bands dimensions
    config = ConfigParser()
    config.read(f'{file_name[:-4]}_config.ini')

    model_dict = {}
    for band in BANDS:
        # Get dimensions
        nAl, nWl = literal_eval(config['DIM'][band])
        al = np.arange(*literal_eval(config['AL'][band]))
        wl = np.arange(*literal_eval(config['WL'][band]))
        # Read feather
        model_rows = pd.read_hdf(f'{file_name[:-4]}_{band}.hdf')
        # Kernel
        kernel = model_rows.iloc[0:nAl].to_numpy()
        # Ensamble
        nE = int(model_rows.iloc[nAl][0])
        iE = model_rows.iloc[nAl+1]
        ensambleKernels = model_rows.iloc[nAl+2:nAl+nE+1].to_numpy()
        model = XpInstrumentModel(al, wl, kernel, ensambleKernels)
        model_dict[band] = model
    return model_dict
