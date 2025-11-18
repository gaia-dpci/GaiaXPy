import pytest

from gaiaxpy import calibrate, plot_spectra
from tests.files.paths import mean_spectrum_avro_file, mean_spectrum_csv_file


@pytest.mark.plotter
def test_multi_absolute_plotter(tmp_path):
    mean_spectra, sampling = calibrate(mean_spectrum_avro_file, save_file=False)
    plot_spectra(mean_spectra, sampling=sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_abs_with_legend', format='pdf', legend=True)
    plot_spectra(mean_spectra, sampling=sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_abs_without_legend', format='pdf', legend=False)


@pytest.mark.plotter
def test_multi_absolute_single_element(tmp_path):
    mean_spectra, sampling = calibrate(mean_spectrum_csv_file, save_file=False)
    plot_spectra(mean_spectra.iloc[[0]], sampling=sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_abs_with_legend_single', format='pdf', legend=True)
    plot_spectra(mean_spectra.iloc[[1]], sampling=sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_abs_without_legend_single', format='pdf', legend=False)


@pytest.mark.plotter
def test_multi_absolute_range_elements(tmp_path):
    mean_spectra, sampling = calibrate(mean_spectrum_csv_file, save_file=False)
    aux_mean_spectra = mean_spectra.iloc[[0, 1]]
    plot_spectra(aux_mean_spectra, sampling=sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_abs_with_legend_range', format='pdf', legend=True)
    plot_spectra(aux_mean_spectra, sampling=sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_abs_without_legend_range', format='pdf', legend=False)
