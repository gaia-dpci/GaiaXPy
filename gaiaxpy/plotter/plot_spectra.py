"""
plot_spectra.py
====================================
Module to plot spectra.
"""

from numpy import ndarray
from .multi_absolute import MultiAbsolutePlotter
from .multi_xp import MultiXpPlotter
from .single import SinglePlotter
from gaiaxpy.core import _warning


def plot_spectra(spectra, sampling=None, multi=False, show_plot=True, output_path=None, file_name=None,
                 format='jpg', legend=True):
    """"
    Plot one or more spectra.

    Args:
        spectra (list): List of spectra to be plotted.
        multi (bool): Generate a multiple subplots. Default value of False plots each
                      spectrum in its own figure. If True, errors will not be plotted.
        show_plot (bool): Show plots if True.
        output_path (str): Path to the directory where the figures will be saved. E.g.:
                         '/home/user/folder'
        file_name (str): Name of the file to be saved.
        format (str): File format for the saved figure. Default value: png.
        legend (bool): Print legend. Valid only if multi is True.
    """
    if sampling is None:
        raise ValueError('A sampling is required.')
    spectra_type = spectra.attrs['data_type'].__name__
    if multi:
        if spectra_type == 'AbsoluteSampledSpectrum':
            plotter = MultiAbsolutePlotter(spectra, sampling, multi, show_plot, output_path, file_name, format, legend)
        elif spectra_type == 'XpSampledSpectrum':
            plotter = MultiXpPlotter(spectra, sampling, multi, show_plot, output_path, file_name, format, legend)
    else:
        plotter = SinglePlotter(spectra, sampling, multi, show_plot, output_path, file_name, format, legend)
    plotter._plot()


def _validate_input(spectra, sampling=None, multi=False, show_plot=True, output_path=None,
                    file_name=None, format='png', legend=True):
    bool_values = [True, False]
    bool_params = [('multi', multi), ('show_plot', show_plot), ('legend', legend)]
    # Format is validated by matplotlib, skip
    if output_path is None and file_name is not None:
        _warning('No save path has been provided, the file will not be saved.')
    if sampling is not None and not isinstance(sampling, ndarray):
        raise ValueError('Sampling must be a NumPy array.')
    for name, variable in bool_params:
        if variable not in bool_values:
            raise ValueError(f'Parameter {name} must be a boolean.')
