"""Evaluate basis functions for internal conversion and external calibration.

A design matrix has shape (n_bases, n_samples): multiplying a coefficient
vector by this matrix produces one flux per sample. Internal conversion uses
pseudo-wavelength positions; external calibration uses wavelengths in nm.
"""

import functools

import numpy as np
from scipy.special import eval_hermite, gamma

from gaiaxpy.core import satellite
from gaiaxpy.core.custom_errors import InvalidReleaseError
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.nature import HC

sqrt_4_pi = np.pi ** (-0.25)


def _get_evaluated_column(basis, wavelength_value, transf_matr, inv_bases_coeffs, pwl_interpolator, resp_interpolator):
    """Evaluate one column of the external-calibration design matrix.

    Args:
        basis (callable): Spline returning all basis values at a pseudo-wavelength.
        wavelength_value (float): Wavelength in nm.
        transf_matr (numpy.ndarray): Basis transformation matrix.
        inv_bases_coeffs (numpy.ndarray): Inverse-basis coefficient matrix.
        pwl_interpolator (callable): Wavelength-to-pseudo-wavelength interpolator.
        resp_interpolator (callable): Response evaluated at a wavelength in nm.

    Returns:
        numpy.ndarray: Transformed inverse-basis values scaled by HC divided by
        wavelength and response. A response whose absolute value is no greater
        than the smallest normal positive float gives a zero reciprocal.
    """

    def __norm(_wavelength_val):
        """Return HC divided by the wavelength supplied in nm."""
        return HC / _wavelength_val

    # Evaluate coordinate and basis coefficients
    coordinate = pwl_interpolator(wavelength_value)
    basis_coeffs = basis(coordinate)
    # Get scaling factors
    v = resp_interpolator(wavelength_value)
    v_norm = 1.0 / v if np.abs(v) > np.finfo(float).tiny else 0.0
    scale = v_norm * __norm(wavelength_value)
    # Apply transformation and projection
    projected = inv_bases_coeffs @ (transf_matr @ basis_coeffs)

    return projected * scale


class SampledBasisFunctions:
    """Store a sample grid and its basis-by-sample design matrix.

    The constructor and getters retain references to their inputs. They do not
    validate dimensions or infer wavelength units.
    """

    def __init__(self, sampling_grid, design_matrix=None):
        """Store the grid and optional design matrix without copying.

        Args:
            sampling_grid (numpy.ndarray): One-dimensional sample positions.
            design_matrix (numpy.ndarray or None): Matrix with one row per basis
                function and one column per sample. None leaves evaluation unset.
        """
        self.sampling_grid = sampling_grid
        self.design_matrix = design_matrix

    @classmethod
    def from_external_instrument_model(cls, sampling, weights, external_instrument_model, xp, release=None,
                                       bases_file=None):
        """Evaluate inverse bases using the external calibration model for one band.

        Args:
            sampling (numpy.ndarray): One-dimensional wavelength grid in nm.
            weights (dict): Per-band weight arrays on the sampling grid. Values at
                zero or negative weights are not evaluated; weight magnitudes are
                not multiplied into the result.
            external_instrument_model (dict): Band models containing dispersion,
                response and inverse-basis configuration.
            xp (str): Lowercase 'bp' or 'rp', used to select the model and weights.
            release (str or None): Explicitly select 'dr3'. None is not
                inferred and raises InvalidReleaseError.
            bases_file (str or pathlib.Path or None): Must be None for DR3.

        Returns:
            SampledBasisFunctions: Grid and externally calibrated design matrix.

        Raises:
            ValueError: A bases_file is supplied for DR3.
            InvalidReleaseError: release is not 'dr3'.

        Notes:
            DR3 evaluates Hermite functions and applies the model response and pupil
            area normalisation. File-reading and model-configuration errors are
            reported to the caller.
        """
        xp_weights = weights[xp]
        xp_ext_instr_model = external_instrument_model[xp]

        n_samples = len(sampling)
        scale = ((xp_ext_instr_model.bases['normRangeMax'] - xp_ext_instr_model.bases['normRangeMin']) /
                 (xp_ext_instr_model.bases['pwlRangeMax'] - xp_ext_instr_model.bases['pwlRangeMin']))
        offset = (xp_ext_instr_model.bases['normRangeMin'] - xp_ext_instr_model.bases['pwlRangeMin'] * scale)

        sampling_pwl = xp_ext_instr_model.wl_to_pwl(sampling)
        rescaled_pwl = (sampling_pwl * scale) + offset

        if release == RELEASES.dr3:
            def __compute_norm(wl):
                """Return the DR3 inverse-response scaling, or zero for a non-positive response."""
                r = xp_ext_instr_model.get_response(wl)
                return HC / (satellite.TELESCOPE_PUPIL_AREA * r * wl) if r > 0 else 0.0

            if bases_file is not None:
                raise ValueError(f'Bases file should be None for DR3 data, but is {bases_file}')
            norm = np.array([__compute_norm(wl) for wl in sampling])
            bases_transformation = xp_ext_instr_model.bases['transformationMatrix']
            evaluated_bases = np.array([_evaluate_hermite_function(n_h, pos, weight) for pos, weight in
                                        zip(rescaled_pwl, xp_weights) for n_h in np.arange(
                    int(xp_ext_instr_model.bases['nInverseBasesCoefficients']))]).reshape(
                n_samples, int(xp_ext_instr_model.bases['nInverseBasesCoefficients']))
            _design_matrix = xp_ext_instr_model.bases['inverseBasesCoefficients'] @ evaluated_bases.T
            transformed_design_matrix = bases_transformation @ _design_matrix
            design_matrix = transformed_design_matrix[:xp_ext_instr_model.bases['nBases']] * norm
        else:
            raise InvalidReleaseError(release)
        return cls(sampling, design_matrix=design_matrix)

    @classmethod
    def from_config(cls, sampling, bases_config):
        """Evaluate configured Hermite bases on a pseudo-wavelength grid.

        Args:
            sampling (numpy.ndarray): One-dimensional pseudo-wavelength positions.
            bases_config (pandas.DataFrame): Basis configuration passed to
                populate_design_matrix.

        Returns:
            SampledBasisFunctions: Grid and calculated basis-by-sample matrix.

        Raises:
            ValueError: The configuration is not a supported Hermite configuration.
        """
        design_matrix = populate_design_matrix(sampling, bases_config)
        return cls(sampling, design_matrix=design_matrix)

    @classmethod
    def from_design_matrix(cls, sampling, design_matrix):
        """Wrap an already calculated design matrix without copying it.

        Args:
            sampling (numpy.ndarray): One-dimensional sample positions.
            design_matrix (numpy.ndarray): Matrix of shape (n_bases, n_samples).

        Returns:
            SampledBasisFunctions: Supplied grid and matrix. Dimensions are not checked.
        """
        return cls(sampling, design_matrix=design_matrix)

    def get_design_matrix(self):
        """Return the stored basis-by-sample matrix without copying.

        Returns:
            numpy.ndarray or None: Value supplied at construction.
        """
        return self.design_matrix

    def get_sampling_grid(self):
        """Return the stored sample-position array without copying.

        Returns:
            numpy.ndarray or None: Value supplied at construction.
        """
        return self.sampling_grid


def _evaluate_hermite_function(n, x, w):
    """Evaluate a Hermite function only where a band's weight is positive.

    Args:
        n (int): Non-negative function index.
        x (float): Normalised coordinate.
        w (float): Band weight, used only to decide whether to evaluate.

    Returns:
        float: Hermite-function value for positive w; otherwise zero.
    """
    return _hermite_function(n, x) if w > 0 else 0


@functools.lru_cache(maxsize=128)
def _hermite_function(n, x):
    """Evaluate a normalised Hermite function by recurrence.

    Args:
        n (int): Non-negative function index.
        x (float): Normalised coordinate. Scalar, hashable inputs are required
            by the result cache.

    Returns:
        float: Gaussian-weighted Hermite-function value. The cache retains up
        to 128 argument combinations.
    """
    if n == 0:
        return sqrt_4_pi * np.exp(-x ** 2. / 2.)
    elif n == 1:
        return sqrt_4_pi * np.exp(-x ** 2. / 2.) * np.sqrt(2.) * x
    c1 = np.sqrt(2. / n) * x
    c2 = -np.sqrt((n - 1) / n)
    return c1 * _hermite_function(n - 1, x) + c2 * _hermite_function(n - 2, x)


def populate_design_matrix(sampling_grid, bases_config):
    """Evaluate the configured internal bases on a pseudo-wavelength grid.

    Args:
        sampling_grid (numpy.ndarray): One-dimensional pseudo-wavelength grid.
        bases_config (pandas.DataFrame): Hermite configuration with dimension,
            transformedSetDimension, range, normalizedRange and
            transformationMatrix fields.

    Returns:
        numpy.ndarray: Matrix of shape (n_output_bases, n_samples), with the
        configured transformation applied.

    Raises:
        ValueError: No supported Hermite basis configuration is recognised.

    Notes:
        The grid is rescaled to the configured normalised range.
        Missing fields and incompatible array shapes raise errors from the
        underlying lookup or calculation.
    """

    def __psi(n, x):
        """Evaluate Gaussian-weighted, normalised Hermite polynomials for broadcast indices and coordinates."""
        return (np.exp(-x ** 2 / 2.0) * eval_hermite(n, x) /
                np.sqrt(np.power(2.0, n) * gamma(n + 1) * np.sqrt(np.pi)))

    bc_columns = bases_config.columns
    if 'knots' not in bc_columns and 'transformedSetDimension' in bc_columns:  # Hermite
        row_config = bases_config.iloc[0]
        normalised_range_lower, normalised_range_upper = row_config['normalizedRange']
        range_lower, range_upper = row_config['range']
        scale = (normalised_range_upper - normalised_range_lower) / (range_upper - range_lower)
        offset = normalised_range_lower - range_lower * scale
        rescaled_pwl = (sampling_grid * scale) + offset

        dimension = int(row_config['dimension'])
        transformed_set_dimension = int(row_config['transformedSetDimension'])
        bases_transformation = row_config['transformationMatrix'].reshape(dimension,
                                                                          transformed_set_dimension)

        design_matrix = __psi(np.arange(dimension)[None, :], rescaled_pwl[:, None])
        return bases_transformation @ design_matrix.T

    raise ValueError('Design matrix cannot be populated from the given configuration.')
