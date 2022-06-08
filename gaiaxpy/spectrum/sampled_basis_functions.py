"""
sampled_basis_functions.py
====================================
Module to represent a set of basis functions evaluated on a grid.
"""

import functools
import math
import numpy as np
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
            sampling_grid (ndarray): 1D array of positions where the bases need to
                be evaluated.
            design_matrix (ndarray): 2D array containing the evaluation of each basis
                at all positions in the sampling grid.
        """
        self.sampling_grid = sampling_grid
        self.design_matrix = design_matrix

    @classmethod
    def from_external_instrument_model(
            cls, sampling, weights, external_instrument_model):
        """
        Instantiate an object starting from a sampling grid, an array of weights and the
        external calibration instrument model.

        Args:
            sampling (ndarray): 1D array of positions where the bases need to
                be evaluated.
            weights (ndarray): 1D array containing the weights to be applied at each
                element in the sampling grid. These are simply used to define where
                in the sampling grid some contribution is expected. Where the weight is
                0, the bases will not be evaluated.
            external_instrument_model (obj): external calibration instrument model.
                This object contains information on the dispersion, response and
                inverse bases.

        Returns:
            object: An instance of this class.
        """
        n_samples = len(sampling)
        scale = (external_instrument_model.bases['normRangeMax'][0] - external_instrument_model.bases['normRangeMin'][0]) / (
            external_instrument_model.bases['pwlRangeMax'][0] - external_instrument_model.bases['pwlRangeMin'][0])
        offset = external_instrument_model.bases['normRangeMin'][0] - \
            external_instrument_model.bases['pwlRangeMin'][0] * scale

        sampling_pwl = external_instrument_model._wl_to_pwl(sampling)
        rescaled_pwl = (sampling_pwl * scale) + offset

        bases_transformation = external_instrument_model.bases['transformationMatrix'][0]
        evaluated_hermite_bases = np.array(
            [
                _evaluate_hermite_function(
                    n_h, pos, weight) for pos, weight in zip(
                    rescaled_pwl, weights) for n_h in np.arange(
                    int(
                        external_instrument_model.bases['nInverseBasesCoefficients'][0]))]) .reshape(
                            n_samples, int(
                                external_instrument_model.bases['nInverseBasesCoefficients'][0]))
        _design_matrix = external_instrument_model.bases['inverseBasesCoefficients'][0]\
            .dot(evaluated_hermite_bases.T)

        transformed_design_matrix = bases_transformation.dot(_design_matrix)

        hc = 1.e9 * nature.C * nature.PLANCK

        def compute_norm(wl):
            r = external_instrument_model._get_response(wl)
            if r > 0:
                return hc / (satellite.TELESCOPE_PUPIL_AREA * r * wl)
            else:
                return 0.

        norm = np.array([compute_norm(wl) for wl in sampling])

        design_matrix = np.zeros(_design_matrix.shape)
        for i in np.arange(external_instrument_model.bases['nBases'][0]):
            design_matrix[i] = transformed_design_matrix[i] * norm

        return cls(sampling, design_matrix=design_matrix)

    @classmethod
    def from_config(cls, sampling, bases_config):
        """
        Instantiate an object starting from a sampling grid and the configuration
        for the basis functions.

        Args:
            sampling (ndarray): 1D array of positions where the bases need to
                be evaluated.
            bases_config (DataFrame): The configuration of the set of bases
                loaded into a DataFrame.

        Returns:
            object: An instance of this class.
        """
        design_matrix = populate_design_matrix(sampling, bases_config)
        return cls(sampling, design_matrix=design_matrix)

    @classmethod
    def from_design_matrix(cls, sampling, design_matrix):
        """
        Instantiate an object starting from a sampling grid and the design
        matrix.

        Args:
            sampling (ndarray): 1D array of positions where the bases need to
                be evaluated.
            design_matrix (ndarray): 2D array containing the evaluation of each basis
                at all positions in the sampling grid.

        Returns:
            object: An instance of this class.
        """
        return cls(sampling, design_matrix=design_matrix)

    def _get_design_matrix(self):
        return self.design_matrix

    def _get_sampling_grid(self):
        return self.sampling_grid


def populate_design_matrix(sampling_grid, config):
    """
    Create a design matrix given the internal calibration bases and a user-defined
    sampling.

    Args:
        sampling_grid (ndarray): 1D array of positions where the bases need to
                be evaluated.
        config (DataFrame): The configuration of the set of bases
                loaded into a DataFrame.

    Returns:
        ndarray: The resulting design matrix.
    """
    n_samples = len(sampling_grid)
    scale = (config['normalizedRange'].iloc(0)[0][1] - config['normalizedRange'].iloc(0)
             [0][0]) / (config['range'].iloc(0)[0][1] - config['range'].iloc(0)[0][0])
    offset = config['normalizedRange'].iloc(0)[0][0] - config['range'].iloc(0)[0][0] * scale
    rescaled_pwl = (sampling_grid * scale) + offset

    def psi(n, x): return 1.0 / np.sqrt(math.pow(2, n) * gamma(n + 1) *
                                         np.sqrt(np.pi)) * np.exp(-x ** 2 / 2.0) * eval_hermite(n, x)

    bases_transformation = config['transformationMatrix'].iloc(0)[0].reshape(
        int(config['dimension']), int(config['transformedSetDimension']))
    design_matrix = np.array([psi(n_h, pos) for pos in rescaled_pwl for n_h in np.arange(
        int(config['dimension']))]).reshape(n_samples, int(config['dimension']))

    return bases_transformation.dot(design_matrix.T)


def _evaluate_hermite_function(n, x, w):
    if w > 0:
        return _hermite_function(n, x)
    else:
        return 0


@functools.lru_cache(maxsize=128)
def _hermite_function(n, x):
    if n == 0:
        return sqrt_4_pi * np.exp(-x ** 2. / 2.)
    elif n == 1:
        return sqrt_4_pi * np.exp(-x ** 2. / 2.) * np.sqrt(2.) * x
    c1 = np.sqrt(2. / n) * x
    c2 = -np.sqrt((n - 1) / n)
    return c1 * _hermite_function(n - 1, x) + c2 * _hermite_function(n - 2, x)
