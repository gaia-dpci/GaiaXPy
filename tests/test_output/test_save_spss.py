import unittest
import numpy as np
import pandas as pd
from gaiaxpy import simulate_continuous, simulate_sampled
from os.path import join
from tests.files import files_path
from .utils import generate_current_md5sum_df

mini_path = join(files_path, 'mini_files')
spss_file = join(mini_path, 'SPSS_mini.csv')
# Create output folder
output_path = 'tests_output_files'
# Load md5sums of the expected output files
md5sum_path = join(files_path, 'md5sum_output_files.csv')
solution_md5sum_df = pd.read_csv(md5sum_path, float_precision='round_trip')

class TestSaveSpss(unittest.TestCase):

    def test_save_output_simulator_sampled(self):
        filename = 'simulator_sampled'
        simulate_sampled(spss_file, save_file=True, sampling=np.linspace(0, 60, 300), output_path=output_path, output_file=filename)
        actual_md5sum_df = generate_current_md5sum_df(output_path)
        filename_str = f'{filename}.csv'
        sampling_str = f'{filename}_sampling.csv'
        # Test data
        expected_md5sum = solution_md5sum_df.loc[solution_md5sum_df['filename'] == filename_str]['hash'].iloc[0]
        actual_md5sum = actual_md5sum_df.loc[actual_md5sum_df['filename'] == filename_str]['hash'].iloc[0]
        self.assertEqual(expected_md5sum, actual_md5sum.decode('utf8'))
        # Test sampling
        expected_md5sum = solution_md5sum_df.loc[solution_md5sum_df['filename'] == sampling_str]['hash'].iloc[0]
        actual_md5sum = actual_md5sum_df.loc[actual_md5sum_df['filename'] == sampling_str]['hash'].iloc[0]
        self.assertEqual(expected_md5sum, actual_md5sum.decode('utf8'))

    def test_save_output_simulator_continuous(self):
        filename = 'simulator_continuous'
        simulate_continuous(spss_file, save_file=True, output_path=output_path, output_file=filename)
        actual_md5sum_df = generate_current_md5sum_df(output_path)
        filename_str = f'{filename}.csv'
        # Test data
        expected_md5sum = solution_md5sum_df.loc[solution_md5sum_df['filename'] == filename_str]['hash'].iloc[0]
        actual_md5sum = actual_md5sum_df.loc[actual_md5sum_df['filename'] == filename_str]['hash'].iloc[0]
        self.assertEqual(expected_md5sum, actual_md5sum.decode('utf8'))
