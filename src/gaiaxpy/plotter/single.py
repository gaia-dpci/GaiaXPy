"""Plot each sampled-spectrum row in its own figure with flux-error shading."""

import matplotlib.pyplot as plt

from .plotter import Plotter


class SinglePlotter(Plotter):
    """Create individual figures for externally or internally calibrated spectra.

    Each input row produces a separate plot, so BP and RP rows from convert are
    plotted independently. Source IDs identify figures through their titles.
    """

    def _plot_single(self, spectrum):
        """Create one figure with a flux line and a flux +/- flux_error shaded region.

        Args:
            spectrum (mapping): Row with source_id and numeric flux/flux_error
                arrays matching the common sampling.

        Notes:
            Axis labels come from the stored spectrum class. The source ID is the
            title. This method creates a figure but does not save or display it.
        """
        spectra_class = self.spectra_class
        source_id = spectrum['source_id']
        fig, ax = plt.subplots(figsize=(16, 9))
        x, y, e = self._get_inputs(spectrum)
        ax.plot(x, y, lw=2, alpha=0.95, label=source_id)
        ax.fill_between(x, y - e, y + e, alpha=0.2)
        ax.set_title('{}'.format(source_id))
        ax.set_xlabel(spectra_class.get_position_label(self.use_tex))
        ax.set_ylabel(spectra_class.get_flux_label(self.use_tex))
        plt.tight_layout()

    def plot_fig(self):
        """Plot each row, saving and/or displaying it according to the stored options.

        Raises:
            ValueError: More than 20 rows are supplied, even when show_plot=False.

        Notes:
            Multiple saved figures use zero-based row suffixes; a single figure
            does not. Saving follows save_file and display follows show_plot.
            The method returns None and closes the current figure after the loop.
        """
        n_spectra = len(self.spectra)
        if n_spectra > self.max_spectra_on_single:
            raise ValueError(
                f'Spectra list is too long. This functionality can only show up to {self.max_spectra_on_single} '
                f'single plots. Try saving the plots without showing them using the option output_path.')
        records = self.spectra.to_dict('records')
        is_len_1 = len(records) == 1
        for index, spectrum in enumerate(records):
            self._plot_single(spectrum)
            if self.save_file:
                index = index if not is_len_1 else None
                self._save_figure(index=index)
            if self.show_plot:
                plt.show()
        plt.close()
