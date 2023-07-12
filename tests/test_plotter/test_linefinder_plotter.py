import shutil
import tempfile
import unittest

import numpy as np

from gaiaxpy.linefinder.linefinder import find_lines, find_extrema
from gaiaxpy.linefinder.plotter import plot_spectra_with_lines
from tests.files.paths import mean_spectrum_csv_file


class TestPlotter(unittest.TestCase):
    # For visual inspection

    def test_lines_plotter(self):
        find_lines(mean_spectrum_csv_file, plot_spectra=True, save_file=False)

    def test_extrema_plotter(self):
        find_extrema(mean_spectrum_csv_file, plot_spectra=True, save_file=False)


class TestPlotterMethod(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_plotter(self):
        source_id = '5762406'
        sampling = np.arange(0, 60)
        wavelength = np.arange(300, 700)
        bp_flux = rp_flux = np.arange(0, 60)
        flux = np.arange(300, 700) * 2e-17
        bp_lines = [('H_beta', 24.42, 4, 24.58, 484.42, 2.5e-16, -7.7e-17, 19.82, 30.63, 3.18e-16, 52.90, 3761.41,
                     1.78)]
        rp_lines = [('H_alpha', 15.73, 2, 15.65, 655.95, 8.1e-17, -2.1e-17, 14.19, 19.57, 1.02e-16, 34.20, 1154.83,
                     2.05)]
        save_plots = True
        plot_spectra_with_lines(source_id, sampling, bp_flux, rp_flux, wavelength, flux, bp_lines, rp_lines,
                                save_plots, output_path=self.temp_dir, prefix='lines')
