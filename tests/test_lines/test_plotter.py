import unittest
import matplotlib.figure as mplf
from os import path

import numpy as np

from gaiaxpy.lines.linefinder import linefinder, extremafinder
from gaiaxpy.lines.plotter import plot_spectra_with_lines

from tests.files.paths import files_path

continuous_path = path.join(files_path, 'xp_continuous')
mean_spectrum_csv = path.join(continuous_path, 'XP_CONTINUOUS_RAW.csv')




class TestPlotter(unittest.TestCase):
    # for visual inspection

    def test_lines_plotter(self):
        lines = linefinder(mean_spectrum_csv, plot_spectra=True)
        
    def test_extrema_plotter(self):
        extrema = extremafinder(mean_spectrum_csv, plot_spectra=True)


class TestPlotterMethod(unittest.TestCase):

    # check if returned object is Figure 
    def test_plotter(self):
       source_id = 5762406957886626816
       sampling = np.arange(0,60)
       wavelength = np.arange(300,700)
       bpflux = rpflux = np.arange(0,60)
       flux = np.arange(300,700) * 2e-17
       continuum = np.arange(300,700) * 1e-17
       bplines = [('H_beta', 24.42, 4, 24.58, 484.42, 2.5e-16, -7.7e-17, 19.82, 30.63, 3.18e-16, 52.90, 3761.41, 1.78)]
       rplines = [('H_alpha', 15.73, 2, 15.65, 655.95, 8.1e-17, -2.1e-17, 14.19, 19.57, 1.02e-16, 34.20, 1154.83, 2.05)]
       save_plots = True
       f = plot_spectra_with_lines(source_id, sampling, bpflux, rpflux, wavelength, flux, continuum, bplines, rplines, save_plots)
       self.assertIsInstance(f, mplf.Figure)

