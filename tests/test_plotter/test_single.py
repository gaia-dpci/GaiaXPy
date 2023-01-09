import unittest
from os import path

from gaiaxpy import calibrate, convert, plot_spectra
from tests.files.paths import files_path

continuous_path = path.join(files_path, 'xp_continuous')
mean_spectrum_avro = path.join(continuous_path, 'MeanSpectrumSolutionWithCov.avro')
mean_spectrum_csv = path.join(continuous_path, 'XP_CONTINUOUS_RAW.csv')


class TestSingle(unittest.TestCase):

    def test_single_xp_plotter(self):
        mean_spectra, sampling = convert(mean_spectrum_avro, save_file=False)
        plot_spectra(mean_spectra, sampling, multi=False, show_plot=False, output_path=None,
                     output_file='single_xp_with_legend_convert', format='pdf', legend=True)
        plot_spectra(mean_spectra, sampling, multi=False, show_plot=False, output_path=None,
                     output_file='single_xp_without_legend_convert', format='pdf', legend=False)

    def test_multi_xp_single_element(self):
        mean_spectra, sampling = convert(mean_spectrum_csv, save_file=False)
        plot_spectra(mean_spectra.iloc[[0]], sampling, multi=False, show_plot=False, output_path=None,
                     output_file='single_xp_with_legend_element', format='pdf', legend=True)
        plot_spectra(mean_spectra.iloc[[1]], sampling, multi=False, show_plot=False, output_path=None,
                     output_file='single_xp_without_legend_element', format='pdf', legend=False)

    def test_multi_absolute_plotter(self):
        mean_spectra, sampling = calibrate(mean_spectrum_avro, save_file=False)
        plot_spectra(mean_spectra, sampling, multi=False, show_plot=False, output_path=None,
                     output_file='single_abs_with_legend', format='pdf', legend=True)
        plot_spectra(mean_spectra, sampling, multi=False, show_plot=False, output_path=None,
                     output_file='single_abs_without_legend', format='pdf', legend=False)

    def test_multi_absolute_single_element(self):
        mean_spectra, sampling = calibrate(mean_spectrum_csv, save_file=False)
        plot_spectra(mean_spectra.iloc[[0]], sampling, multi=False, show_plot=False, output_path=None,
                     output_file='single_abs_with_legend_element', format='pdf', legend=True)
        plot_spectra(mean_spectra.iloc[[1]], sampling, multi=False, show_plot=False, output_path=None,
                     output_file='single_abs_without_legend_element', format='pdf', legend=False)
