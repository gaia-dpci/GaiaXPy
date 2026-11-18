"""Share sampled-spectrum data, axis-label selection and figure saving."""

from os.path import join
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


class Plotter:
    """Hold plotting options and common helpers for concrete plot layouts.

    The spectrum class in attrs['data_type'] supplies axis-label methods. Plotting
    uses Matplotlib's current figure for saving; subclasses create the figures.
    """

    def __init__(self, spectra, sampling, show_plot, output_path, output_file, _format, legend, save_file,
                 use_tex=False):
        """Store spectrum data, output settings and layout limits.

        Args:
            spectra (pandas.DataFrame or pandas.Series): Sampled-spectrum table
                retaining attrs['data_type']. A Series is converted to a one-row
                DataFrame before the spectrum class is read.
            sampling (numpy.ndarray): Common positions for every spectrum row.
            show_plot (bool): Whether to call pyplot.show after plotting.
            output_path (str, pathlib.Path or None): Destination directory, or None.
            output_file (str or None): Filename stem, or None for the class name.
            _format (str): Matplotlib output format, without a leading dot.
            legend (bool): Include a legend in combined plots.
            save_file (bool): Whether saving was requested.
            use_tex (bool): Ask the spectrum class for LaTeX labels; defaults to False.

        Notes:
            Row limits are 40 for combined display with a legend and 20 for
            individual figures. Construction stores the settings but does not
            validate array shapes or create figures.
        """
        if isinstance(spectra, pd.Series):
            df = spectra.reset_index().transpose()
            df.columns = df.iloc[0]
            spectra = df[1:]
        self.spectra = spectra
        self.spectra_class = _set_class(spectra)
        self.sampling = sampling
        self.show_plot = show_plot
        self.output_path = output_path
        # Here we assume that the list only contains spectra of the same type
        self.output_file = self._set_output_file(output_file)
        self.format = _format
        self.legend = legend
        self.save_file = save_file
        self.use_tex = use_tex
        # Set maximum number of spectra to plot
        self.max_spectra_on_multi = 40
        self.max_spectra_on_single = 20

    def plot_fig(self):
        """Reject direct plotting through the base class with NotImplementedError."""
        raise NotImplementedError('Method not implemented for the parent class.')

    def _get_inputs(self, spectrum):
        """Return the common sampling and a row's flux and flux_error values.

        Args:
            spectrum (mapping): Sampled-spectrum row with flux and flux_error keys.

        Returns:
            tuple: Sampling positions, flux array and flux-error array. Fields
            are accessed directly without conversion or shape validation.
        """
        return self.sampling, spectrum['flux'], spectrum['flux_error']

    def _save_figure(self, index=None):
        """Save Matplotlib's current figure using the configured path, stem and format.

        Args:
            index (int or None): Optional zero-based row number appended to the
                filename stem. None adds no suffix.

        Notes:
            Use the current directory if no output_path is supplied. Create missing
            parent directories and save with transparent=False. This helper does
            not check save_file; the calling layout decides whether to save.
        """
        # Save the figure in the current path is no path is provided
        output_path = self.output_path if self.output_path else '.'
        # If index is provided, then append to file name
        output_file_name = f'{self.output_file}_{index}' if index is not None else self.output_file
        Path(output_path).mkdir(parents=True, exist_ok=True)
        plt.savefig(join(output_path, f'{output_file_name}.{self.format}'), format=self.format, transparent=False)

    def _set_output_file(self, output_file):
        """Return a supplied non-empty filename stem, otherwise the spectrum-class name."""
        return output_file if output_file else self.spectra_class.__name__


def _set_class(spectra):
    """Read the spectrum class from a DataFrame's data_type attribute.

    Args:
        spectra (pandas.DataFrame): Table with attrs['data_type'] set to a
            spectrum class providing get_position_label and get_flux_label.

    Returns:
        type: Stored spectrum class, without constructing an instance.

    Raises:
        ValueError: Input is not a DataFrame.
        KeyError: data_type is missing from attrs.
    """
    if isinstance(spectra, pd.DataFrame):
        return spectra.attrs['data_type']
    else:
        raise ValueError('Input should be a pandas DataFrame.')
