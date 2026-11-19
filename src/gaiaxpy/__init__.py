# flake8: noqa
from .core.version import __version__

__all__ = [
    "__version__",
    "get_required_columns",
    "calibrate",
    "convert",
    "generate",
    "plot_spectra",
    "apply_error_correction",
    "PhotometricSystem",
    "load_additional_systems",
    "remove_additional_systems",
    "get_chi2",
    "get_inverse_covariance_matrix",
    "get_inverse_square_root_covariance_matrix",
    "pwl_to_wl",
    "wl_to_pwl",
    "pwl_range",
    "wl_range"
]


def __getattr__(name):
    if name == 'get_required_columns':
        from .input_reader.required_columns import get_required_columns
        return get_required_columns

    if name == "calibrate":
        from .calibrator.calibrator import calibrate
        return calibrate

    if name == "generate":
        from .generator.generator import generate
        return generate

    if name in {"PhotometricSystem", "load_additional_systems", "remove_additional_systems"}:
        from .photometric_system.photometric_system import (
            PhotometricSystem,
            load_additional_systems,
            remove_additional_systems
        )
        return locals()[name]

    if name == "convert":
        from .converter.converter import convert
        return convert

    if name == "plot_spectra":
        from .plotter.plot_spectra import plot_spectra
        return plot_spectra

    if name == "apply_error_correction":
        from .error_correction.error_corrector import apply_error_correction
        return apply_error_correction

    if name in {
        "get_chi2",
        "get_inverse_covariance_matrix",
        "get_inverse_square_root_covariance_matrix"
    }:
        from .cholesky.cholesky import (
            get_chi2,
            get_inverse_covariance_matrix,
            get_inverse_square_root_covariance_matrix
        )
        return locals()[name]

    if name in {"pwl_to_wl", "wl_to_pwl", "pwl_range", "wl_range"}:
        from .core.dispersion_function import pwl_to_wl, wl_to_pwl, pwl_range, wl_range
        return locals()[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
