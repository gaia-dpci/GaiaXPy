import unittest
from os import path

from gaiaxpy import calibrate, plot_spectra
from tests.files.paths import files_path

continuous_path = path.join(files_path, 'xp_continuous')
mean_spectrum_avro = path.join(continuous_path, 'MeanSpectrumSolutionWithCov.avro')
mean_spectrum_csv = path.join(continuous_path, 'XP_CONTINUOUS_RAW.csv')


class TestMultiAbsolute(unittest.TestCase):

    def test_multi_absolute_plotter(self):
        mean_spectra, sampling = calibrate(mean_spectrum_avro, save_file=False)
        plot_spectra(mean_spectra, sampling=sampling, multi=True, show_plot=False, output_path=None,
                     output_file='multi_abs_with_legend', format='pdf', legend=True)
        plot_spectra(mean_spectra, sampling=sampling, multi=True, show_plot=False, output_path=None,
                     output_file='multi_abs_without_legend', format='pdf', legend=False)

    def test_multi_absolute_single_element(self):
        mean_spectra, sampling = calibrate(mean_spectrum_csv, save_file=False)
        plot_spectra(mean_spectra.iloc[[0]], sampling=sampling, multi=True, show_plot=False, output_path=None,
                     output_file='multi_abs_with_legend_single', format='pdf', legend=True)
        plot_spectra(mean_spectra.iloc[[1]], sampling=sampling, multi=True, show_plot=False, output_path=None,
                     output_file='multi_abs_without_legend_single', format='pdf', legend=False)

    def test_multi_absolute_range_elements(self):
        mean_spectra, sampling = calibrate(mean_spectrum_csv, save_file=False)
        index_list = list(range(2))
        aux_mean_spectra = mean_spectra.iloc[index_list]
        plot_spectra(aux_mean_spectra, sampling=sampling, multi=True, show_plot=False, output_path=None,
                     output_file='multi_abs_with_legend_range', format='pdf', legend=True)
        plot_spectra(aux_mean_spectra, sampling=sampling, multi=True, show_plot=False, output_path=None,
                     output_file='multi_abs_without_legend_range', format='pdf', legend=False)
