"""
multi_xp.py
====================================
Module to plot multiple XP spectra.
"""

from .plotter import Plotter
from gaiaxpy.core.satellite import BANDS
import matplotlib.pyplot as plt

class MultiXpPlotter(Plotter):

    def _plot_multi_xp(self):
        legend = self.legend
        spectra_df = self.spectra
        spectra_class = self.spectra_class
        max_flux = 0
        fig, ax = plt.subplots(ncols=2, figsize=(16, 8))
        # Set titles
        ax[0].set_title(BANDS.bp.upper())
        ax[1].set_title(BANDS.rp.upper())
        ax[1].yaxis.set_label_position('right')
        ax[1].yaxis.tick_right()
        for index, spectrum in spectra_df.iterrows():
            x, y, e = self._get_inputs(spectrum)
            max_flux = max(y) if max(y) > max_flux else max_flux
            if spectrum.xp in [BANDS.bp, BANDS.bp.upper()]:
                ax[0].plot(x, y, lw=2, alpha=0.95, label=spectrum.source_id)
            elif spectrum.xp == [BANDS.rp, BANDS.rp.upper()]:
                ax[1].plot(x, y, lw=2, alpha=0.95, label=spectrum.source_id)
        for axis in ax:
            axis.set_ylim(0, 1.05 * max_flux)
            axis.set_xlabel(spectra_class._get_position_label())
            axis.set_ylabel(spectra_class._get_flux_label())
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
                fig.legend(lines, labels, bbox_to_anchor=(1, 1), loc='upper right', borderaxespad=0.1)

    def _plot(self):
        n_spectra = len(self.spectra)
        if self.show_plot and self.legend and n_spectra > self.max_spectra_on_multi:
            raise ValueError(f'The legend can only be shown for a list of spectra no longer than {self.max_spectra_on_multi} elements. Try setting legend to False or retry with a shorter list.')
        self._plot_multi_xp()
        if self.save_path:
            self._save_figure(self.save_path, self.file_name, self.format)
        if self.show_plot:
            plt.show()
        plt.close()
