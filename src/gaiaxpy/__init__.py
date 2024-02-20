# flake8: noqa
try:
    from ._version import version as __version__
    from ._version import version_tuple
except ImportError:
    __version__ = 'unknown version'
    version_tuple = (0, 0, __version__)

from .calibrator.calibrator import calibrate
from .cholesky.cholesky import get_chi2, get_inverse_covariance_matrix, get_inverse_square_root_covariance_matrix
from .converter.converter import convert
from .core.dispersion_function import pwl_to_wl, wl_to_pwl, pwl_range, wl_range
from .error_correction.error_correction import apply_error_correction
from .generator.generator import generate
from .generator.photometric_system import PhotometricSystem, load_additional_systems, remove_additional_systems
from .linefinder.linefinder import find_extrema, find_fast, find_lines
from .plotter.plot_spectra import plot_spectra
