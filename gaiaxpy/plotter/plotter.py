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

    def __init__(self, spectra, sampling, multi, show_plot, output_path, file_name, format, legend):
        self.spectra = spectra
        self.spectra_class = _set_class(spectra)
        self.sampling = sampling
        self.multi = multi
        self.show_plot = show_plot
        self.output_path = output_path
        # Here we assume that the list only contains spectra of the same type
        self.file_name = self._set_file_name(file_name)
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

    def _save_figure(self, output_path, file_name, format):
        if output_path:
            Path(output_path).mkdir(parents=True, exist_ok=True)
            plt.savefig(
                join(output_path, f'{file_name}.{format}'),
                format=format,
                transparent=False)

    def _set_file_name(self, file_name):
        if not file_name:
            file_name = self.spectra_class.__name__
        return file_name


def _set_class(spectra):
    if isinstance(spectra, pd.DataFrame):
        return spectra.attrs['data_type']
    # Any other iterable
    else:
        raise ValueError('Input should be pd.DataFrame.')
