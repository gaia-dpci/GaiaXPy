import unittest
from os.path import join

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import calibrate
from gaiaxpy.core.generic_functions import str_to_array, correlation_to_covariance
from tests.files.paths import files_path

f = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv')

# Load sampling
sampling_solution = join(files_path, 'calibrator_solution', 'calibrate_with_covariance_solution_sampling.csv')
converters = {'pos': (lambda x: str_to_array(x))}
sampling_solution_array = pd.read_csv(sampling_solution, float_precision='round_trip',
                                      converters=converters).iloc[0]['pos']

_atol, _rtol = 1e-10, 1e-10


class TestCalibratorWithCovariance(unittest.TestCase):

    def test_with_covariance(self):
        spectra, sampling = calibrate(f, with_correlation=True, save_file=False)
        # spectra = spectra.drop(index=1)  # Drop row containing nans as it doesn't add new information when testing
        # Load spectra
        _converters = {key: (lambda x: str_to_array(x)) for key in ['flux', 'flux_error', 'covariance']}
        solution = join(files_path, 'calibrator_solution', 'calibrate_with_covariance_solution.csv')
        solution_df = pd.read_csv(solution, float_precision='round_trip', converters=_converters)
        # solution_df = solution_df.drop(index=1)
        stdev_pairs = [(1.1224667, 1.3151282), 1.0339215, (1.0479343, 1.0767492)]

        def scale_error(error_array, stdevs):
            if isinstance(stdevs, float):
                error_array = error_array / stdevs
            elif len(stdevs) == 2:
                midpoint = len(error_array) // 2
                error_array[:midpoint] /= stdevs[0]  # divide the first half by stdev[0]
                error_array[midpoint:] /= stdevs[1]  # divide the second half by stdev[1]
            return error_array

        scaled_errors = [scale_error(arr, devs) for arr, devs in
                         zip(spectra['flux_error'].values, stdev_pairs)]

        # Stdevs are one because the errors are already scaled
        spectra['covariance'] = [correlation_to_covariance(corr, err, st) for corr, err, st in
                                 zip(spectra['correlation'].values, scaled_errors, np.ones(3))]
        spectra = spectra.drop(columns=['correlation'])
        npt.assert_array_equal(sampling, sampling_solution_array)

        spectra = spectra.drop(index=1)
        solution_df = solution_df.drop(index=1)

        pdt.assert_frame_equal(spectra.loc[:, spectra.columns != 'covariance'],
                               solution_df.loc[:, solution_df.columns != 'covariance'], atol=_atol, rtol=_rtol)

        for actual_cov, solution_cov in zip(spectra['covariance'].values, solution_df['covariance'].values):
            # Issues with all close, so this approach was used instead
            num_close = np.sum(np.isclose(actual_cov, solution_cov, rtol=_rtol))
            total_num = actual_cov.shape[0] * actual_cov.shape[1]
            self.assertEqual(num_close, total_num)
