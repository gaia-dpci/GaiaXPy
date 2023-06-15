"""
plot_spectra.py
====================================
Module to plot spectra.
"""
import warnings
from pathlib import Path
from typing import Optional, Union

import pandas as pd
from numpy import ndarray

from .multi_absolute import MultiAbsolutePlotter
from .multi_xp import MultiXpPlotter
from .single import SinglePlotter


def __plot_multi(spectra_type: str, spectra: pd.DataFrame, sampling: ndarray, show_plot: bool,
                 output_path: Optional[Union[Path, str]], output_file: Optional[str], format: str, legend: bool,
                 save_file: bool):
    if spectra_type == 'AbsoluteSampledSpectrum':
        plotter = MultiAbsolutePlotter(spectra, sampling, show_plot, output_path, output_file, format,
                                       legend, save_file)
    elif spectra_type == 'XpSampledSpectrum':
        plotter = MultiXpPlotter(spectra, sampling, show_plot, output_path, output_file, format, legend, save_file)
    else:
        raise ValueError('Unrecognised spectra type.')
    return plotter


def plot_spectra(spectra: pd.DataFrame, sampling: ndarray = None, multi: bool = False, show_plot: bool = True,
                 output_path: Optional[Union[Path, str]] = None, output_file: Optional[str] = None, format: str = None,
                 legend: bool = True):
    """
    Plot one or more spectra.

    Args:
        spectra (DataFrame): DataFrame of spectra to be plotted.
        sampling (ndarray): Sampling used to create the spectra.
        multi (bool): Generate a multiple subplots. Default value of False plots each spectrum in its own figure. If
            True, errors will not be plotted.
        show_plot (bool): Show plots if True.
        output_path (str): Path to the directory where the figures will be saved. E.g.: '/home/user/folder'
        output_file (str): Name of the output file without extension (e.g. 'my_plot').
        format (str): File format for the saved figure. Defaults to 'jpg'.
        legend (bool): Print legend. Valid only if multi is True.
    """
    if sampling is None:
        raise ValueError('A sampling is required.')
    # If the user passes an argument related to saving the file, then assume the user wants the plot to be saved
    save_file = bool(output_path) or bool(output_file) or bool(format)
    if not save_file and not show_plot:
        warnings.warn("No values have been provided to save the file: output_path, output_file or format. The "
                      "parameter show_plot is set to False. The function will not generate a plot.", stacklevel=2)
        return
    format = format if format else 'jpg'
    if multi:
        plotter = __plot_multi(spectra.attrs['data_type'].__name__, spectra, sampling, show_plot,
                               output_path, output_file, format, legend, save_file)
    else:
        plotter = SinglePlotter(spectra, sampling, show_plot, output_path, output_file, format, legend, save_file)
    plotter.plot_fig()
