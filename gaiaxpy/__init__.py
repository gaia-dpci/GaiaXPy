from .calibrator.calibrator import calibrate
from .colour_equation.xp_filter_system_colour_equation import apply_colour_equation
from .converter.converter import convert
from .error_correction import apply_error_correction
from .generator.generator import generate
from .generator.photometric_system import PhotometricSystem
from .plotter.plot_spectra import plot_spectra
from .simulator.simulator import simulate_continuous, simulate_sampled

__version__ = '0.1.0'
