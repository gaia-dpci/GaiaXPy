import shutil
import tempfile
import unittest

from gaiaxpy import calibrate, plot_spectra
from tests.files.paths import mean_spectrum_avro_file, mean_spectrum_csv_file


class TestMultiAbsolute(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_multi_absolute_plotter(self):
        mean_spectra, sampling = calibrate(mean_spectrum_avro_file, save_file=False)
        plot_spectra(mean_spectra, sampling=sampling, multi=True, show_plot=True, output_path=self.temp_dir,
                     output_file='multi_abs_with_legend', format='pdf', legend=True)
        plot_spectra(mean_spectra, sampling=sampling, multi=True, show_plot=True, output_path=self.temp_dir,
                     output_file='multi_abs_without_legend', format='pdf', legend=False)

    def test_multi_absolute_single_element(self):
        mean_spectra, sampling = calibrate(mean_spectrum_csv_file, save_file=False)
        plot_spectra(mean_spectra.iloc[[0]], sampling=sampling, multi=True, show_plot=True, output_path=self.temp_dir,
                     output_file='multi_abs_with_legend_single', format='pdf', legend=True)
        plot_spectra(mean_spectra.iloc[[1]], sampling=sampling, multi=True, show_plot=True, output_path=self.temp_dir,
                     output_file='multi_abs_without_legend_single', format='pdf', legend=False)

    def test_multi_absolute_range_elements(self):
        mean_spectra, sampling = calibrate(mean_spectrum_csv_file, save_file=False)
        index_list = list(range(2))
        aux_mean_spectra = mean_spectra.iloc[index_list]
        plot_spectra(aux_mean_spectra, sampling=sampling, multi=True, show_plot=True, output_path=self.temp_dir,
                     output_file='multi_abs_with_legend_range', format='pdf', legend=True)
        plot_spectra(aux_mean_spectra, sampling=sampling, multi=True, show_plot=True, output_path=self.temp_dir,
                     output_file='multi_abs_without_legend_range', format='pdf', legend=False)
