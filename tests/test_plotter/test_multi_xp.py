import unittest
import numpy as np
from os import path
from gaiaxpy import convert, simulate_sampled, plot_spectra
from tests.files import files_path

continuous_path = path.join(files_path, 'xp_continuous')
mean_spectrum_avro = path.join(continuous_path, 'MeanSpectrumSolutionWithCov.avro')
mean_spectrum_csv = path.join(continuous_path, 'XP_CONTINUOUS_RAW_dr3int6.csv')
sed_csv = path.join(files_path, 'mini_files', 'SPSS_mini.csv')

class TestMultiXp(unittest.TestCase):

    def test_multi_xp_plotter_convert(self):
        mean_spectra, sampling = convert(mean_spectrum_avro, save_file=False)
        plot_spectra(mean_spectra, sampling, multi=True, show_plot=False, output_path=None, file_name='multi_xp_with_legend', format='pdf', legend=True)
        plot_spectra(mean_spectra, sampling, multi=True, show_plot=False, output_path=None, file_name='multi_xp_without_legend', format='pdf', legend=False)

    def test_multi_xp_single_element_convert(self):
        mean_spectra, sampling = convert(mean_spectrum_csv, save_file=False)
        plot_spectra(mean_spectra.iloc[[0]], sampling, multi=True, show_plot=False, output_path=None, file_name='multi_xp_with_legend_single', format='pdf', legend=True)
        plot_spectra(mean_spectra.iloc[[1]], sampling, multi=True, show_plot=False, output_path=None, file_name='multi_xp_without_legend_single', format='pdf', legend=False)

    def test_multi_xp_plotter_simulate_sampled(self):
        simulated_data, positions = simulate_sampled(sed_csv, sampling=np.linspace(0, 60, 300), save_file=False)
        index_list = list(range(2))
        aux_simulated = simulated_data.iloc[index_list]
        plot_spectra(aux_simulated, positions, multi=True, show_plot=False, output_path=None, file_name='multi_xp_with_legend', format='pdf', legend=True)
        plot_spectra(aux_simulated, positions, multi=True, show_plot=False, output_path=None, file_name='multi_xp_without_legend', format='pdf', legend=False)
