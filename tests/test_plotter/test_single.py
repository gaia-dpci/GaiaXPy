import matplotlib.pyplot as plt
import pytest

from gaiaxpy import calibrate, convert, plot_spectra
from gaiaxpy.core.generic_variables import RELEASES
from tests.files.continuous import dr3_mean_spectra_avro_file, dr3_mean_spectra_csv_file


@pytest.mark.plotter
def test_single_xp_plotter(tmp_path):
    mean_spectra, sampling = convert(dr3_mean_spectra_avro_file, save_file=False, release=RELEASES.dr3)
    plot_spectra(mean_spectra, sampling, multi=False, show_plot=True, output_path=tmp_path,
                 output_file='single_xp_with_legend_convert', format='pdf', legend=True)
    plot_spectra(mean_spectra, sampling, multi=False, show_plot=True, output_path=tmp_path,
                 output_file='single_xp_without_legend_convert', format='pdf', legend=False)


@pytest.mark.plotter
def test_multi_xp_single_element(tmp_path):
    mean_spectra, sampling = convert(dr3_mean_spectra_csv_file, save_file=False, release=RELEASES.dr3)
    plot_spectra(mean_spectra.iloc[[0]], sampling, multi=False, show_plot=True, output_path=tmp_path,
                 output_file='single_xp_with_legend_element', format='pdf', legend=True)
    plot_spectra(mean_spectra.iloc[[1]], sampling, multi=False, show_plot=True, output_path=tmp_path,
                 output_file='single_xp_without_legend_element', format='pdf', legend=False)


@pytest.mark.plotter
def test_multi_absolute_plotter(tmp_path):
    mean_spectra, sampling = calibrate(dr3_mean_spectra_avro_file, save_file=False, release=RELEASES.dr3)
    plot_spectra(mean_spectra, sampling, multi=False, show_plot=True, output_path=tmp_path,
                 output_file='single_abs_with_legend', format='pdf', legend=True)
    plot_spectra(mean_spectra, sampling, multi=False, show_plot=True, output_path=tmp_path,
                 output_file='single_abs_without_legend', format='pdf', legend=False)


@pytest.mark.plotter
def test_multi_absolute_single_element(tmp_path):
    mean_spectra, sampling = calibrate(dr3_mean_spectra_csv_file, save_file=False, release=RELEASES.dr3)
    plot_spectra(mean_spectra.iloc[[0]], sampling, multi=False, show_plot=True, output_path=tmp_path,
                 output_file='single_abs_with_legend_element', format='pdf', legend=True)
    plot_spectra(mean_spectra.iloc[[1]], sampling, multi=False, show_plot=True, output_path=tmp_path,
                 output_file='single_abs_without_legend_element', format='pdf', legend=False)


def test_use_tex_is_opt_in_and_scoped(monkeypatch):
    mean_spectra, sampling = convert(dr3_mean_spectra_csv_file, save_file=False, release=RELEASES.dr3)
    original_usetex = plt.rcParams['text.usetex']
    observed = []

    def plot_fig(plotter):
        observed.append((plotter.use_tex, plt.rcParams['text.usetex']))

    monkeypatch.setattr('gaiaxpy.plotter.single.SinglePlotter.plot_fig', plot_fig)

    plot_spectra(mean_spectra.iloc[[0]], sampling, show_plot=True)
    plot_spectra(mean_spectra.iloc[[0]], sampling, show_plot=True, use_tex=True)

    assert observed == [(False, False), (True, True)]
    assert plt.rcParams['text.usetex'] == original_usetex
