import unittest
import pandas as pd
import numpy.testing as npt
import pandas.testing as pdt
from os.path import join
from gaiaxpy import calibrate
from gaiaxpy.core.generic_functions import str_to_array
from tests.files import files_path
from tests.utils import pos_file_to_array


# Load XP continuous file
continuous_path = join(files_path, 'xp_continuous')
missing_bp_file = join(continuous_path, 'XP_CONTINUOUS_RAW_with_missing_BP.csv')

# Load solution
solution_path = join(files_path, 'calibrator_solution')
converters = dict([(column, lambda x: str_to_array(x)) for column in ['flux', 'flux_error']])
solution_df = pd.read_csv(join(solution_path, 'with_missing_calibrator_solution.csv'), \
                          converters=converters)
solution_sampling = pos_file_to_array(join(solution_path, 'with_missing_calibrator_solution_sampling.csv'))

class TestCalibratorMissingBP(unittest.TestCase):

    def test_missing_bp_file(self):
        output_df, sampling = calibrate(missing_bp_file, save_file=False)
        pdt.assert_frame_equal(output_df, solution_df)
        npt.assert_array_equal(sampling, solution_sampling)
