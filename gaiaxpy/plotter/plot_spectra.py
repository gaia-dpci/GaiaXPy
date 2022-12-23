"""
plot_spectra.py
====================================
Module to plot spectra.
"""

from numpy import ndarray

from .multi_absolute import MultiAbsolutePlotter
from .multi_xp import MultiXpPlotter
from .single import SinglePlotter


def plot_spectra(spectra, sampling=None, multi=False, show_plot=True, output_path=None, output_file=None,
                 format='jpg', legend=True):
    """
    Plot one or more spectra.

    Args:
        spectra (DataFrame): DataFrame of spectra to be plotted.
        sampling (ndarray): Sampling used to create the spectra.
        multi (bool): Generate a multiple subplots. Default value of False plots each spectrum in its own figure. If
            True, errors will not be plotted.
        show_plot (bool): Show plots if True.
        output_path (str): Path to the directory where the figures will be saved. E.g.: '/home/user/folder'
        output_file (str): Name of the file to be saved.
        format (str): File format for the saved figure. Default value: png.
        legend (bool): Print legend. Valid only if multi is True.
    """
    if sampling is None:
        raise ValueError('A sampling is required.')
    spectra_type = spectra.attrs['data_type'].__name__
    if multi:
        if spectra_type == 'AbsoluteSampledSpectrum':
            plotter = MultiAbsolutePlotter(spectra, sampling, multi, show_plot, output_path, output_file, format,
                                           legend)
        elif spectra_type == 'XpSampledSpectrum':
            plotter = MultiXpPlotter(spectra, sampling, multi, show_plot, output_path, output_file, format, legend)
        else:
            raise ValueError('Unrecognised spectra type.')
    else:
        plotter = SinglePlotter(spectra, sampling, multi, show_plot, output_path, output_file, format, legend)
    plotter._plot()
