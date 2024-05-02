"""
sampled_basis_functions.py
====================================
Module to represent a set of basis functions evaluated on a grid.
"""

import functools
import math

import numpy as np
from scipy.interpolate import BSpline
from scipy.special import eval_hermite, gamma

from gaiaxpy.core import nature, satellite

sqrt_4_pi = np.pi ** (-0.25)


class SampledBasisFunctions(object):
    """
    Evaluation of a set of basis functions on a user-defined grid.
    """

    def __init__(self, sampling_grid, design_matrix=None):
        """
        Initialise a sampled basis functions object.

        Args:
            sampling_grid (ndarray): 1D array of positions where the bases need to be evaluated.
            design_matrix (ndarray): 2D array containing the evaluation of each basis at all positions in the sampling
                grid.
        """
        self.sampling_grid = sampling_grid
        self.design_matrix = design_matrix

    @classmethod
    def from_external_instrument_model(cls, sampling, weights, external_instrument_model):
        """
        Instantiate an object starting from a sampling grid, an array of weights and the external calibration instrument
            model.

        Args:
            sampling (ndarray): 1D array of positions where the bases need to be evaluated.
            weights (ndarray): 1D array containing the weights to be applied at each element in the sampling grid. These
                are simply used to define where in the sampling grid some contribution is expected. Where the weight is
                0, the bases will not be evaluated.
            external_instrument_model (obj): external calibration instrument model. This object contains information on
                the dispersion, response and inverse bases.

        Returns:
            SampledBasisFunctions: An instance of this class.
        """
        n_samples = len(sampling)
        scale = ((external_instrument_model.bases['normRangeMax'] -
                  external_instrument_model.bases['normRangeMin']) /
                 (external_instrument_model.bases['pwlRangeMax'] -
                  external_instrument_model.bases['pwlRangeMin']))
        offset = (external_instrument_model.bases['normRangeMin'] -
                  external_instrument_model.bases['pwlRangeMin'] * scale)

        sampling_pwl = external_instrument_model.wl_to_pwl(sampling)
        rescaled_pwl = (sampling_pwl * scale) + offset

        bases_transformation = external_instrument_model.bases['transformationMatrix']
        evaluated_hermite_bases = np.array([_evaluate_hermite_function(n_h, pos, weight) for pos, weight in
                                            zip(rescaled_pwl, weights) for n_h in np.arange(
                int(external_instrument_model.bases['nInverseBasesCoefficients']))]).reshape(
            n_samples, int(external_instrument_model.bases['nInverseBasesCoefficients']))
        _design_matrix = external_instrument_model.bases['inverseBasesCoefficients'] @ evaluated_hermite_bases.T
        transformed_design_matrix = bases_transformation @ _design_matrix

        hc = 1.e9 * nature.C * nature.PLANCK

        def compute_norm(wl):
            r = external_instrument_model.get_response(wl)
            if r > 0:
                return hc / (satellite.TELESCOPE_PUPIL_AREA * r * wl)
            else:
                return 0.0

        norm = np.array([compute_norm(wl) for wl in sampling])
        design_matrix = np.array([transformed_design_matrix[i] * norm for i in
                                  np.arange(external_instrument_model.bases['nBases'])])

        return cls(sampling, design_matrix=design_matrix)

    @classmethod
    def from_config(cls, sampling, bases_config):
        """
        Instantiate an object starting from a sampling grid and the configuration for the basis functions.

        Args:
            sampling (ndarray): 1D array of positions where the bases need to be evaluated.
            bases_config (DataFrame): The configuration of the set of bases loaded into a DataFrame.

        Returns:
            object: An instance of this class.
        """
        design_matrix = populate_design_matrix(sampling, bases_config)
        return cls(sampling, design_matrix=design_matrix)

    @classmethod
    def from_design_matrix(cls, sampling, design_matrix):
        """
        Instantiate an object starting from a sampling grid and the design matrix.

        Args:
            sampling (ndarray): 1D array of positions where the bases need to be evaluated.
            design_matrix (ndarray): 2D array containing the evaluation of each basis at all positions in the sampling
                grid.

        Returns:
            object: An instance of this class.
        """
        return cls(sampling, design_matrix=design_matrix)

    def get_design_matrix(self):
        return self.design_matrix

    def get_sampling_grid(self):
        return self.sampling_grid


def _evaluate_hermite_function(n, x, w):
    return _hermite_function(n, x) if w > 0 else 0


@functools.lru_cache(maxsize=128)
def _hermite_function(n, x):
    if n == 0:
        return sqrt_4_pi * np.exp(-x ** 2. / 2.)
    elif n == 1:
        return sqrt_4_pi * np.exp(-x ** 2. / 2.) * np.sqrt(2.) * x
    c1 = np.sqrt(2. / n) * x
    c2 = -np.sqrt((n - 1) / n)
    return c1 * _hermite_function(n - 1, x) + c2 * _hermite_function(n - 2, x)


def populate_design_matrix(sampling_grid, bases_config):
    def __psi(n, x):
        return (1.0 / np.sqrt(math.pow(2, n) * gamma(n + 1) * np.sqrt(np.pi)) * np.exp(-x ** 2 / 2.0) *
                eval_hermite(n, x))

    n_samples = len(sampling_grid)
    bc_columns = bases_config.columns
    if 'knots' not in bc_columns and 'transformedSetDimension' in bc_columns:  # Hermite
        normalised_range_lower, normalised_range_upper = bases_config['normalizedRange'].iloc(0)[0]
        range_lower, range_upper = bases_config['range'].iloc(0)[0]
        scale = (normalised_range_upper - normalised_range_lower) / (range_upper - range_lower)
        offset = normalised_range_lower - range_lower * scale
        rescaled_pwl = (sampling_grid * scale) + offset
        dimension = int(bases_config['dimension'].iloc[0])
        transformed_set_dimension = int(bases_config['transformedSetDimension'].iloc[0])
        bases_transformation = bases_config['transformationMatrix'].iloc(0)[0].reshape(dimension,
                                                                                       transformed_set_dimension)
        design_matrix = np.array([__psi(n_h, pos) for pos in rescaled_pwl for n_h in np.arange(dimension)]).reshape(
            n_samples, dimension)
        return bases_transformation @ design_matrix.T
    elif 'knots' in bc_columns:  # Spline
        if len(bases_config) != 1:
            raise ValueError('Only one row should be accepted at a time.')
        knots = bases_config['knots'].iloc[0]
        n_knots = len(knots)
        order = bases_config['order'].iloc[0]
        degree = order - 1
        n_bases = n_knots - order
        if 'transformationMatrix' in bases_config.__dir__():
            transformation_matrix = np.array(bases_config.transformationMatrix.values[0])
            ts_dim = bases_config.transformedSetDimension.values[0]
            bases_transformation = transformation_matrix.reshape(ts_dim, n_bases)
        else:
            bases_transformation = np.identity(n_bases)
        design_matrix = np.zeros((n_bases, n_samples))

        for basis_id in np.arange(n_bases):  # Evaluate
            c = np.zeros(n_knots)
            c[basis_id] = 1.0
            basis = BSpline(knots, c, degree)
            design_matrix[basis_id] = np.array([basis(pos) for pos in sampling_grid])
        return bases_transformation.dot(design_matrix)
    else:
        raise ValueError('Design matrix cannot be populated from the given configuration.')
