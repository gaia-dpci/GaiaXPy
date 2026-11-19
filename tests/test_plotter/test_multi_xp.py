import pytest

from gaiaxpy import convert, plot_spectra
from gaiaxpy.core.generic_variables import RELEASES
from tests.files.continuous import dr3_mean_spectra_avro_file, dr3_mean_spectra_csv_file


@pytest.mark.plotter
def test_multi_xp_plotter_convert(tmp_path):
    mean_spectra, sampling = convert(dr3_mean_spectra_avro_file, save_file=False, release=RELEASES.dr3)
    plot_spectra(mean_spectra, sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_xp_with_legend', format='pdf', legend=True)
    plot_spectra(mean_spectra, sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_xp_without_legend', format='pdf', legend=False)


@pytest.mark.plotter
def test_multi_xp_single_element_convert(tmp_path):
    mean_spectra, sampling = convert(dr3_mean_spectra_csv_file, save_file=False, release=RELEASES.dr3)
    plot_spectra(mean_spectra.iloc[[0]], sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_xp_with_legend_single', format='pdf', legend=True)
    plot_spectra(mean_spectra.iloc[[1]], sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_xp_without_legend_single', format='pdf', legend=False)


def test_multi_xp_keeps_source_colours_with_missing_band():
    import matplotlib.pyplot as plt
    import pandas as pd

    from gaiaxpy.plotter.multi_xp import MultiXpPlotter
    from gaiaxpy.spectrum.xp_sampled_spectrum import XpSampledSpectrum

    spectra = pd.DataFrame([
        {'source_id': 1, 'xp': 'BP', 'flux': [1.0, 2.0], 'flux_error': [0.1, 0.1]},
        {'source_id': 1, 'xp': 'RP', 'flux': [2.0, 3.0], 'flux_error': [0.1, 0.1]},
        {'source_id': 2, 'xp': 'RP', 'flux': [3.0, 4.0], 'flux_error': [0.1, 0.1]},
        {'source_id': 3, 'xp': 'BP', 'flux': [4.0, 5.0], 'flux_error': [0.1, 0.1]},
        {'source_id': 3, 'xp': 'RP', 'flux': [5.0, 6.0], 'flux_error': [0.1, 0.1]},
    ])
    spectra.attrs['data_type'] = XpSampledSpectrum

    plotter = MultiXpPlotter(
        spectra, [1.0, 2.0], False, None, None, 'pdf', True, False
    )
    plotter._plot_multi_xp()

    fig = plt.gcf()
    bp_ax, rp_ax = fig.axes

    # BP contains sources 1 and 3.
    bp_source_1 = bp_ax.lines[0]
    bp_source_3 = bp_ax.lines[1]

    # RP contains sources 1, 2 and 3.
    rp_source_1 = rp_ax.lines[0]
    rp_source_2 = rp_ax.lines[1]
    rp_source_3 = rp_ax.lines[2]

    # A source must keep the same colour across BP and RP.
    assert bp_source_1.get_color() == rp_source_1.get_color()
    assert bp_source_3.get_color() == rp_source_3.get_color()

    # All sources, including the RP-only source, must appear in the legend.
    legend = fig.legends[0]
    assert {text.get_text() for text in legend.get_texts()} == {'1', '2', '3'}

    # The RP-only source's legend colour must match its plotted line.
    legend_colours = {
        text.get_text(): handle.get_color()
        for text, handle in zip(legend.get_texts(), legend.legend_handles)
    }
    assert legend_colours['2'] == rp_source_2.get_color()

    plt.close(fig)


def test_multi_xp_skips_missing_flux():
    import matplotlib.pyplot as plt
    import pandas as pd

    from gaiaxpy.plotter.multi_xp import MultiXpPlotter
    from gaiaxpy.spectrum.xp_sampled_spectrum import XpSampledSpectrum

    spectra = pd.DataFrame([
        {'source_id': 1, 'xp': 'BP', 'flux': None, 'flux_error': None},
        {'source_id': 1, 'xp': 'RP', 'flux': [2.0, 3.0], 'flux_error': [0.1, 0.1]},
    ])
    spectra.attrs['data_type'] = XpSampledSpectrum

    plotter = MultiXpPlotter(
        spectra, [1.0, 2.0], False, None, None, 'pdf', True, False
    )
    plotter._plot_multi_xp()

    fig = plt.gcf()
    bp_ax, rp_ax = fig.axes
    assert len(bp_ax.lines) == 0
    assert len(rp_ax.lines) == 1
    plt.close(fig)
