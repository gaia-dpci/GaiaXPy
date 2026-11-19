"""Plot multiple internally calibrated spectra in separate BP and RP panels."""

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from gaiaxpy.core.satellite import BANDS
from .plotter import Plotter


class MultiXpPlotter(Plotter):
    """Use a consistent source colour across the two photometer panels."""

    def _plot_multi_xp(self):
        """Create BP/RP panels, assigning colours by the first occurrence of each source ID.

        Rows are directed by their case-insensitive xp label. Skip rows with flux=None,
        keep one legend entry per source, and cycle the combined tab20 palettes when
        needed. Both panels start at zero and share an upper limit of 1.05 times the
        largest positive plotted flux. Flux errors are read but not drawn. The method
        returns None and leaves its figure current without saving or displaying it.
        """
        show_legend = self.legend
        spectra_df = self.spectra
        spectra_class = self.spectra_class
        max_flux = 0

        fig, ax = plt.subplots(ncols=2, figsize=(16, 8))

        source_ids = spectra_df['source_id'].drop_duplicates().tolist()

        colours = (list(plt.colormaps['tab20'].colors) + list(plt.colormaps['tab20b'].colors)
                   + list(plt.colormaps['tab20c'].colors))

        source_colours = {
            source_id: colours[index % len(colours)]
            for index, source_id in enumerate(source_ids)
        }

        # Set titles
        ax[0].set_title(BANDS.bp.upper())
        ax[1].set_title(BANDS.rp.upper())
        ax[1].yaxis.set_label_position('right')
        ax[1].yaxis.tick_right()

        for spectrum in spectra_df.to_dict('records'):
            x, y, e = self._get_inputs(spectrum)

            # A source may only have one of BP/RP. Missing bands should not prevent the available spectrum from
            # being plotted.
            if y is None:
                continue

            max_flux = max(y) if max(y) > max_flux else max_flux

            axis = BANDS.index(spectrum['xp'].lower())
            source_id = spectrum['source_id']

            ax[axis].plot(x, y, lw=2, alpha=0.95, color=source_colours[source_id])

        for axis in ax:
            axis.set_ylim(0, 1.05 * max_flux)
            axis.set_xlabel(spectra_class.get_position_label(self.use_tex))
            axis.set_ylabel(spectra_class.get_flux_label(self.use_tex))

        if show_legend:
            # Construct the legend directly from the source/colour mapping rather than from either subplot.
            handles = [Line2D([0], [0], color=source_colours[source_id], lw=2, label=str(source_id))
                       for source_id in source_ids]

            fig.subplots_adjust(top=0.95, bottom=0.05, left=0.05, right=0.82, wspace=0.020)

            fig.legend(
                handles=handles,
                bbox_to_anchor=(1, 1),
                loc='upper right',
                borderaxespad=0.1,
                fontsize=10,
                handlelength=3
            )

    def plot_fig(self):
        """Create the BP/RP figure, optionally save/display it, then close it.

        Raises:
            ValueError: More than 40 rows are supplied while both show_plot and
                legend are True.

        Notes:
            Saving currently depends on a non-empty output_path or output_file,
            rather than save_file. Supplying format alone through plot_spectra
            therefore does not save this layout. The method returns None.
        """
        n_spectra = len(self.spectra)
        if self.show_plot and self.legend and n_spectra > self.max_spectra_on_multi:
            raise ValueError(f'The legend can only be shown for a list of spectra no longer than '
                             f'{self.max_spectra_on_multi} elements. Try setting legend to False or retry with a '
                             f'shorter list.')

        self._plot_multi_xp()

        if self.save_file:
            self._save_figure()

        if self.show_plot:
            plt.show()

        plt.close()
