import unittest

from gaiaxpy import convert, plot_spectra
from tests.files.paths import output_path, mean_spectrum_avro_file, mean_spectrum_csv_file


class TestMultiXp(unittest.TestCase):

    def test_multi_xp_plotter_convert(self):
        mean_spectra, sampling = convert(mean_spectrum_avro_file, save_file=False)
        plot_spectra(mean_spectra, sampling, multi=True, show_plot=True, output_path=output_path,
                     output_file='multi_xp_with_legend', format='pdf', legend=True)
        plot_spectra(mean_spectra, sampling, multi=True, show_plot=True, output_path=output_path,
                     output_file='multi_xp_without_legend', format='pdf', legend=False)

    def test_multi_xp_single_element_convert(self):
        mean_spectra, sampling = convert(mean_spectrum_csv_file, save_file=False)
        plot_spectra(mean_spectra.iloc[[0]], sampling, multi=True, show_plot=True, output_path=output_path,
                     output_file='multi_xp_with_legend_single', format='pdf', legend=True)
        plot_spectra(mean_spectra.iloc[[1]], sampling, multi=True, show_plot=True, output_path=output_path,
                     output_file='multi_xp_without_legend_single', format='pdf', legend=False)
