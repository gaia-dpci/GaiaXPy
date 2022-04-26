import unittest
from os import path
from gaiaxpy.simulator import simulate_continuous, simulate_sampled
from tests.files import files_path
from tests.utils import df_columns_to_array
import numpy as np
import numpy.testing as npt
import pandas.testing as pdt
from numpy import ndarray
import pandas as pd

# Avoid warning, false positive when assigning values to dfs
pd.options.mode.chained_assignment = None

len_coefficients = 55
sources = [1]
#sources = [1, 5, 7, \
#           8, 9, 10, \
#           16, 20, 14, \
#           19]

# String to array
def string_to_array(string):
    return np.fromstring(string[1:-1], sep=',')

def is_array(value):
    return isinstance(value, str) and value[0] == '('

def parse_pmn_file(filepath):
    df = pd.read_csv(filepath, float_precision='round_trip')
    # Take first row
    first_row = df.iloc[0]
    columns_to_parse = []
    for column in df.columns:
        if is_array(first_row[column]):
            columns_to_parse.append(column)
    for index, row in df.iterrows():
        for column in columns_to_parse:
            df[column][index] = string_to_array(row[column])
    return df

spss_path = path.join(files_path, 'spss')
#spss_full = path.join(spss_path, 'SPSS_full.csv')
#spss_1nm = path.join(spss_path, 'SPSS_1nm.csv')
#spss_2nm = path.join(spss_path, 'SPSS_2nm.csv')
spss_sed = path.join(spss_path, 'SPSS_sample.csv')

sampling = np.arange(0, 60, 0.125)
#sampled_output_full, _ = simulate_sampled(spss_full, save_file=False, sampling=sampling)
#sampled_output_1nm, _ = simulate_sampled(spss_1nm, save_file=False, sampling=sampling)
#sampled_output_2nm, _ = simulate_sampled(spss_2nm, save_file=False, sampling=sampling)
sampled_output, _ = simulate_sampled(spss_sed, save_file=False, sampling=sampling)
sampled_output = sampled_output[sampled_output['source_id']==1]

atol = 1e-7
rtol = 1e-7

# Load solutions
solution_folder = 'simulator_solution'
continuous_full_solution_path = path.join(files_path, solution_folder, 'continuous_full_solution.csv')
simulator_continuous_full_solution_df = pd.read_csv(continuous_full_solution_path, float_precision='round_trip')
columns_to_parse = ['bp_coefficients', 'bp_coefficient_correlations', \
                    'bp_coefficient_errors', 'rp_coefficients', \
                    'rp_coefficient_correlations', 'rp_coefficient_errors']
simulator_continuous_full_solution_df = df_columns_to_array(simulator_continuous_full_solution_df, columns_to_parse)

simulator_sampled_full_solution_path = path.join(files_path, solution_folder, 'sampled_full_0_60_0125_solution.csv')
simulator_sampled_full_solution_df = pd.read_csv(simulator_sampled_full_solution_path, float_precision='round_trip')
columns_to_parse = ['flux', 'flux_error']
simulator_sampled_full_solution_df = df_columns_to_array(simulator_sampled_full_solution_df, columns_to_parse)

class TestSampledSimulator(unittest.TestCase):

    def test_wrong_sampling_upper(self):
        sampling = np.linspace(0, 75, 300)
        with self.assertRaises(ValueError):
            sampled_output, _ = simulate_sampled(spss_sed, save_file=False, sampling=sampling)

    def test_wrong_sampling_lower(self):
        sampling = np.linspace(-11, 60, 300)
        with self.assertRaises(ValueError):
            sampled_output, _ = simulate_sampled(spss_sed, save_file=False, sampling=sampling)

    def test_simulate_sampled_full(self):
        self.assertIsInstance(sampled_output, pd.DataFrame)
        pdt.assert_frame_equal(sampled_output, simulator_sampled_full_solution_df)

#    def test_simulate_sampled_1nm(self):
#        self.assertIsInstance(sampled_output_1nm, pd.DataFrame)
#        self.assertTrue((sampled_output_1nm.columns == simulator_sampled_full_solution_df.columns).all())

#    def test_simulate_sampled_2nm(self):
#        self.assertIsInstance(sampled_output_2nm, pd.DataFrame)
#        self.assertTrue((sampled_output_2nm.columns == simulator_sampled_full_solution_df.columns).all())

    def test_simulate_sampled_sampling(self):
        _, positions = simulate_sampled(spss_sed, save_file=False, sampling=sampling)
        npt.assert_array_equal(positions, sampling)
