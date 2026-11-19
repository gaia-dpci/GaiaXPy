import pytest

from gaiaxpy import calibrate, plot_spectra
from gaiaxpy.core.generic_variables import RELEASES
from tests.files.continuous import dr3_mean_spectra_avro_file, dr3_mean_spectra_csv_file


@pytest.mark.plotter
def test_multi_absolute_plotter(tmp_path):
    mean_spectra, sampling = calibrate(dr3_mean_spectra_avro_file, save_file=False, release=RELEASES.dr3)
    plot_spectra(mean_spectra, sampling=sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_abs_with_legend', format='pdf', legend=True)
    plot_spectra(mean_spectra, sampling=sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_abs_without_legend', format='pdf', legend=False)


@pytest.mark.plotter
def test_multi_absolute_single_element(tmp_path):
    mean_spectra, sampling = calibrate(dr3_mean_spectra_csv_file, save_file=False, release=RELEASES.dr3)
    plot_spectra(mean_spectra.iloc[[0]], sampling=sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_abs_with_legend_single', format='pdf', legend=True)
    plot_spectra(mean_spectra.iloc[[1]], sampling=sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_abs_without_legend_single', format='pdf', legend=False)


@pytest.mark.plotter
def test_multi_absolute_range_elements(tmp_path):
    mean_spectra, sampling = calibrate(dr3_mean_spectra_csv_file, save_file=False, release=RELEASES.dr3)
    aux_mean_spectra = mean_spectra.iloc[[0, 1]]
    plot_spectra(aux_mean_spectra, sampling=sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_abs_with_legend_range', format='pdf', legend=True)
    plot_spectra(aux_mean_spectra, sampling=sampling, multi=True, show_plot=True, output_path=tmp_path,
                 output_file='multi_abs_without_legend_range', format='pdf', legend=False)
