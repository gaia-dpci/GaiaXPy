from .calibrator.calibrator import calibrate
from .converter.converter import convert
from .core import pwl_to_wl, wl_to_pwl, pwl_range, wl_range
from .error_correction import apply_error_correction
from .generator.generator import generate
from .generator.photometric_system import PhotometricSystem
from .plotter.plot_spectra import plot_spectra

__version__ = '1.1.0'
