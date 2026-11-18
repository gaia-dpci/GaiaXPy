"""Choose the plot layout and display or save sampled-spectrum figures.

Externally calibrated spectra can share a single set of axes. Internally
calibrated BP/RP spectra use separate panels in combined mode. Individual mode
creates one figure per input row. These functions plot sampled arrays; they
do not read files, retrieve source IDs or evaluate continuous spectra.
"""
import warnings
from pathlib import Path
from typing import Optional, Union

import matplotlib.pyplot as plt
from numpy import ndarray

from .multi_absolute import MultiAbsolutePlotter
from .multi_xp import MultiXpPlotter
from .single import SinglePlotter


def __plot_multi(spectra_type: str, spectra: 'pd.DataFrame', sampling: ndarray, show_plot: bool,
                 output_path: Optional[Union[Path, str]], output_file: Optional[str], format: str, legend: bool,
                 save_file: bool, use_tex: bool):
    """Select a combined-spectrum plotter from the stored spectrum-class name.

    Args:
        spectra_type (str): Spectrum class name from attrs['data_type'].
            Names containing AbsoluteSampledSpectrum select one shared set of
            axes; XpSampledSpectrum selects separate BP/RP panels.
        spectra (pandas.DataFrame): Sampled spectra with flux and flux_error
            arrays and source_id. XP spectra also require xp labels.
        sampling (numpy.ndarray): Common positions for the flux arrays.
        show_plot (bool): Display the combined figure.
        output_path (str, pathlib.Path or None): Optional output directory.
        output_file (str or None): Optional filename stem.
        format (str): Matplotlib output format.
        legend (bool): Include a source legend.
        save_file (bool): Whether saving was requested by the public function.
        use_tex (bool): Use LaTeX labels within the public function's rc_context.

    Returns:
        Plotter: Configured MultiAbsolutePlotter or MultiXpPlotter. This helper
        does not create a figure itself.

    Raises:
        ValueError: The spectrum-class name is unsupported.
    """
    if 'AbsoluteSampledSpectrum' in spectra_type:
        plotter = MultiAbsolutePlotter(spectra, sampling, show_plot, output_path, output_file, format,
                                       legend, save_file, use_tex)
    elif spectra_type == 'XpSampledSpectrum':
        plotter = MultiXpPlotter(spectra, sampling, show_plot, output_path, output_file, format, legend, save_file,
                                 use_tex)
    else:
        raise ValueError('Unrecognised spectra type.')
    return plotter


def plot_spectra(spectra: 'pd.DataFrame', sampling: ndarray = None, multi: bool = False, show_plot: bool = True,
                 output_path: Optional[Union[Path, str]] = None, output_file: Optional[str] = None, format: str = None,
                 legend: bool = True, use_tex: bool = False):
    """Display or save plots of sampled spectra from calibrate or convert.

    Args:
        spectra (pandas.DataFrame): Sampled spectra with source_id, flux and
            flux_error columns. Each flux/error cell must contain a numeric
            array matching sampling. Keep attrs['data_type'] from the operation
            that produced the table; it supplies the spectrum class and labels.
            Internally calibrated spectra also require xp ('BP' or 'RP') for
            combined plots. Files, queries and source-ID lists or tuples are
            not accepted as spectrum input.
        sampling (numpy.ndarray): Common sampling positions returned with the
            spectra: wavelength in nm for calibrate, pseudo-wavelength for
            convert. Supply this explicitly; None raises ValueError.
        multi (bool): False, the default, creates a figure for every input row
            with a shaded flux +/- flux_error region. True combines spectra
            without error shading: one panel for externally calibrated spectra,
            or separate BP/RP panels for internally calibrated spectra.
        show_plot (bool): Display figures; defaults to True. False can be used
            to save without displaying when output arguments are supplied.
        output_path (str, pathlib.Path or None): Output directory. Supplying a
            non-empty path requests saving, creating directories as needed.
            When saving without a path, use the current directory.
        output_file (str or None): Filename stem without an extension. A
            non-empty value requests saving. If omitted, use the spectrum
            class name. Multiple individual figures receive zero-based suffixes
            such as _0 and _1; one individual or combined figure has no suffix.
        format (str or None): Matplotlib output format, such as 'jpg', 'png'
            or 'pdf'. Defaults to 'jpg'. A supplied format requests saving,
            except that a combined XP plot also requires output_path or
            output_file in the current implementation.
        legend (bool): Show the source legend in combined mode; defaults to
            True. Individual figures identify each source in the title instead.
        use_tex (bool): Render text using LaTeX; defaults to False. True needs
            a working LaTeX installation.

    Returns:
        None: Figures are displayed and/or saved, not returned.

    Raises:
        ValueError: Sampling is missing, the input type or combined spectrum
            type is unsupported, or the requested layout exceeds its row limit.
        KeyError: Required columns or attrs['data_type'] are absent.

    Notes:
        Individual mode accepts at most 20 rows, including when only saving.
        Combined mode limits the input to 40 rows only when both show_plot and
        legend are True. These limits count rows, not distinct source IDs;
        convert normally supplies separate BP and RP rows for each source.

        In a combined XP plot, a source keeps the same colour in both panels;
        rows with flux=None are skipped. Both panels use a common y-axis range
        starting at zero. Combined plots still access flux_error even though
        they do not draw it.

        If show_plot=False and no output argument requests saving, issue a
        UserWarning and return without creating a plot. Shape mismatches and
        rendering, LaTeX or file-writing errors reach the caller.
    """
    if sampling is None:
        raise ValueError('A sampling is required.')
    # If the user passes an argument related to saving the file, then assume the user wants the plot to be saved
    save_file = bool(output_path) or bool(output_file) or bool(format)
    if not save_file and not show_plot:
        warnings.warn("No values have been provided to save the file: output_path, output_file or format. The "
                      "parameter show_plot is set to False. The function will not generate a plot.", stacklevel=2)
        return
    format = format if format else 'jpg'
    if multi:
        plotter = __plot_multi(spectra.attrs['data_type'].__name__, spectra, sampling, show_plot,
                               output_path, output_file, format, legend, save_file, use_tex)
    else:
        plotter = SinglePlotter(spectra, sampling, show_plot, output_path, output_file, format, legend, save_file,
                                use_tex)
    with plt.rc_context({'text.usetex': use_tex}):
        plotter.plot_fig()
