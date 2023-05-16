import unittest
from os.path import join

import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import convert
from gaiaxpy.core.generic_functions import str_to_array, correlation_to_covariance
from tests.files.paths import files_path

f = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_with_missing_BP.csv')
# Load spectra
converters = {key: (lambda x: str_to_array(x)) for key in ['flux', 'flux_error', 'covariance']}
solution = join(files_path, 'converter_solution', 'converter_with_covariance_missing_bp_solution.csv')
solution_df = pd.read_csv(solution, float_precision='round_trip', converters=converters)

# Load sampling
sampling_solution = join(files_path, 'converter_solution', 'converter_with_covariance_missing_bp_solution_sampling.csv')
converters = {'pos': (lambda x: str_to_array(x))}
sampling_solution_array = pd.read_csv(sampling_solution, float_precision='round_trip',
                                      converters=converters).iloc[0]['pos']

_atol, _rtol = 1e-10, 1e-10


class TestConverterWithCovariance(unittest.TestCase):

    def test_with_covariance(self):
        output_spectra, sampling = convert(f, with_correlation=True, save_file=False)
        output_spectra['covariance'] = output_spectra.apply(lambda row: correlation_to_covariance(
            row['correlation'], row['flux_error'], row['standard_deviation']), axis=1)
        output_spectra = output_spectra.drop(columns=['correlation', 'standard_deviation'])
        pdt.assert_frame_equal(output_spectra, solution_df, atol=_atol, rtol=_rtol)
        npt.assert_array_equal(sampling, sampling_solution_array)
