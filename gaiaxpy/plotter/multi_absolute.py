"""
multi_absolute.py
====================================
Module to plot multiple absolute spectra.
"""

from .plotter import Plotter
import matplotlib.pyplot as plt


class MultiAbsolutePlotter(Plotter):

    def _plot_multi_absolute(self):
        spectra_class = self.spectra_class
        spectra_df = self.spectra
        fig, ax = plt.subplots(figsize=(16, 9))
        for index, spectrum in spectra_df.iterrows():
            x, y, e = self._get_inputs(spectrum)
            ax.plot(x, y, lw=2, alpha=0.95, label=spectrum.source_id)
        ax.set_xlabel(spectra_class._get_position_label())
        ax.set_ylabel(spectra_class._get_flux_label())
        fig.tight_layout()
        if self.legend:
            lines = set()
            labels = set()
            for ax in fig.axes:
                ax_line, ax_label = ax.get_legend_handles_labels()
                lines.update(ax_line)
                labels.update(ax_label)
            fig.subplots_adjust(
                top=0.95,
                bottom=0.05,
                left=0.05,
                right=0.85,
                wspace=0.020)
            fig.legend(lines, labels, bbox_to_anchor=(1, 1), loc='upper right', borderaxespad=1.0)
        return fig, ax

    def _plot(self):
        n_spectra = len(self.spectra)
        if self.show_plot and self.legend and n_spectra > self.max_spectra_on_multi:
            raise ValueError(f'The legend can only be shown for a list of spectra no longer than {self.max_spectra_on_multi} elements. Try setting legend to False or retry with a shorter list.')
        fig, ax = self._plot_multi_absolute()
        if self.output_path:
            self._save_figure(self.output_path, self.file_name, self.format)
        if self.show_plot:
            plt.show()
        plt.close()
