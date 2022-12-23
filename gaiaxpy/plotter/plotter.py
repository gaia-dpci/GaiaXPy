"""
plotter.py
====================================
Module to create a plotter object.
"""

from os.path import join
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


class Plotter(object):

    def __init__(self, spectra, sampling, multi, show_plot, output_path, output_file, _format, legend):
        self.spectra = spectra
        self.spectra_class = _set_class(spectra)
        self.sampling = sampling
        self.multi = multi
        self.show_plot = show_plot
        self.output_path = output_path
        # Here we assume that the list only contains spectra of the same type
        self.output_file = self._set_output_file(output_file)
        self.format = _format
        self.legend = legend
        self.max_spectra_on_multi = 40
        self.max_spectra_on_single = 20

    def _plot(self):
        raise NotImplementedError('Method not implemented for the parent class.')

    def _get_inputs(self, spectrum):
        return self.sampling, spectrum['flux'], spectrum['flux_error']

    def _get_source_id(self, spectrum):
        return spectrum['source_id']

    def _save_figure(self, output_path, output_file, _format):
        if output_path:
            Path(output_path).mkdir(parents=True, exist_ok=True)
            plt.savefig(join(output_path, f'{output_file}.{_format}'), format=_format, transparent=False)

    def _set_output_file(self, output_file):
        return output_file if output_file else self.spectra_class.__name__


def _set_class(spectra):
    if isinstance(spectra, pd.DataFrame):
        return spectra.attrs['data_type']
    else:
        raise ValueError('Input should be a pandas DataFrame.')
