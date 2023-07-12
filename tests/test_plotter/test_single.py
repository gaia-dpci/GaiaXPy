import shutil
import tempfile
import unittest

from gaiaxpy import calibrate, convert, plot_spectra
from tests.files.paths import mean_spectrum_avro_file, mean_spectrum_csv_file


class TestSingle(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_single_xp_plotter(self):
        mean_spectra, sampling = convert(mean_spectrum_avro_file, save_file=False)
        plot_spectra(mean_spectra, sampling, multi=False, show_plot=True, output_path=self.temp_dir,
                     output_file='single_xp_with_legend_convert', format='pdf', legend=True)
        plot_spectra(mean_spectra, sampling, multi=False, show_plot=True, output_path=self.temp_dir,
                     output_file='single_xp_without_legend_convert', format='pdf', legend=False)

    def test_multi_xp_single_element(self):
        mean_spectra, sampling = convert(mean_spectrum_csv_file, save_file=False)
        plot_spectra(mean_spectra.iloc[[0]], sampling, multi=False, show_plot=True, output_path=self.temp_dir,
                     output_file='single_xp_with_legend_element', format='pdf', legend=True)
        plot_spectra(mean_spectra.iloc[[1]], sampling, multi=False, show_plot=True, output_path=self.temp_dir,
                     output_file='single_xp_without_legend_element', format='pdf', legend=False)

    def test_multi_absolute_plotter(self):
        mean_spectra, sampling = calibrate(mean_spectrum_avro_file, save_file=False)
        plot_spectra(mean_spectra, sampling, multi=False, show_plot=True, output_path=self.temp_dir,
                     output_file='single_abs_with_legend', format='pdf', legend=True)
        plot_spectra(mean_spectra, sampling, multi=False, show_plot=True, output_path=self.temp_dir,
                     output_file='single_abs_without_legend', format='pdf', legend=False)

    def test_multi_absolute_single_element(self):
        mean_spectra, sampling = calibrate(mean_spectrum_csv_file, save_file=False)
        plot_spectra(mean_spectra.iloc[[0]], sampling, multi=False, show_plot=True, output_path=self.temp_dir,
                     output_file='single_abs_with_legend_element', format='pdf', legend=True)
        plot_spectra(mean_spectra.iloc[[1]], sampling, multi=False, show_plot=True, output_path=self.temp_dir,
                     output_file='single_abs_without_legend_element', format='pdf', legend=False)
