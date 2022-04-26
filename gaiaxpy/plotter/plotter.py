"""
plotter.py
====================================
Module to create a plotter object.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from os.path import join

class Plotter(object):

    def __init__(self, spectra, sampling, multi, show_plot, save_path, file_name, format, legend):
        self.spectra = spectra
        self.spectra_class = _set_class(spectra)
        self.sampling = sampling
        self.multi = multi
        self.show_plot = show_plot
        self.save_path = save_path
        # Here we assume that the list only contains spectra of the same type
        self.file_name = _set_file_name(file_name, spectra)
        self.format = format
        self.legend = legend
        self.max_spectra_on_multi = 40
        self.max_spectra_on_single = 20

    def _plot(self):
        raise NotImplementedError('Method not implemented for the parent class.')

    def _get_inputs(self, spectrum):
        return self.sampling, spectrum['flux'], spectrum['flux_error']

    def _get_source_id(self, spectrum):
        return spectrum['source_id']

    def _save_figure(self, save_path, file_name, format):
        if save_path:
            Path(save_path).mkdir(parents=True, exist_ok=True)
            plt.savefig(
                join(save_path, f'{file_name}.{format}'),
                format=format,
                transparent=False)

def _spectra_as_list(spectra):
    if isinstance(spectra, list):
        return spectra
    else:
        return [spectra] # to list

def _set_file_name(file_name, spectra):
    if not file_name:
        try:
            spectrum = spectra[0]
        except:
            # Case of a single object
            spectrum = spectra
        file_name = spectrum.__class__.__name__
    return file_name

def _set_class(spectra):
    if isinstance(spectra, pd.DataFrame):
        return spectra.attrs['data_type']
    # Any other iterable
    else:
        raise ValueError('Input should be pd.DataFrame.')
