import unittest
from os import path

from gaiaxpy import convert, plot_spectra
from tests.files.paths import files_path

continuous_path = path.join(files_path, 'xp_continuous')
mean_spectrum_avro = path.join(continuous_path, 'MeanSpectrumSolutionWithCov.avro')
mean_spectrum_csv = path.join(continuous_path, 'XP_CONTINUOUS_RAW.csv')


class TestMultiXp(unittest.TestCase):

    def test_multi_xp_plotter_convert(self):
        mean_spectra, sampling = convert(mean_spectrum_avro, save_file=False)
        plot_spectra(mean_spectra, sampling, multi=True, show_plot=False, output_path=None,
                     output_file='multi_xp_with_legend', format='pdf', legend=True)
        plot_spectra(mean_spectra, sampling, multi=True, show_plot=False, output_path=None,
                     output_file='multi_xp_without_legend', format='pdf', legend=False)

    def test_multi_xp_single_element_convert(self):
        mean_spectra, sampling = convert(mean_spectrum_csv, save_file=False)
        plot_spectra(mean_spectra.iloc[[0]], sampling, multi=True, show_plot=False, output_path=None,
                     output_file='multi_xp_with_legend_single', format='pdf', legend=True)
        plot_spectra(mean_spectra.iloc[[1]], sampling, multi=True, show_plot=False, output_path=None,
                     output_file='multi_xp_without_legend_single', format='pdf', legend=False)
