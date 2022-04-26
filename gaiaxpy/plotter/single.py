"""
single.py
====================================
Module to plot a single spectrum, either absolute or XP.
"""

from .plotter import Plotter
import matplotlib.pyplot as plt


class SinglePlotter(Plotter):

    '''
    for index, spectrum in spectra_df.iterrows():
        x, y, e = self._get_inputs(spectrum)
        ax.plot(x, y, lw=2, alpha=0.95, label=spectrum.source_id)
    '''

    def _plot_single(self, spectrum):
        spectra_class = self.spectra_class
        source_id = spectrum.source_id
        fig, ax = plt.subplots(figsize=(16, 9))
        x, y, e = self._get_inputs(spectrum)
        ax.plot(x, y, lw=2, alpha=0.95, label=source_id)
        ax.fill_between(x, y - e, y + e, alpha=0.2)
        ax.set_title('{}'.format(source_id))
        ax.set_xlabel(spectra_class._get_position_label())
        ax.set_ylabel(spectra_class._get_flux_label())
        plt.tight_layout()

    def _plot(self):
        n_spectra = len(self.spectra)
        if n_spectra > self.max_spectra_on_single:
            raise ValueError(f'Spectra list is too long. This functionality can only show up to {self.max_spectra_on_single} single plots. Try saving the plots without showing them using the option output_path.')
        for index, spectrum in self.spectra.iterrows():
            self._plot_single(spectrum)
            if self.output_path:
                if n_spectra > 1:
                    self._save_figure(self.output_path, f'{self.file_name}_{index}', self.format)
                else:
                    self._save_figure(self.output_path, self.file_name, self.format)
        if self.show_plot:
            plt.show()
        plt.close()
