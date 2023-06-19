from os.path import join

import pandas as pd

from tests.files.paths import files_path, continuous_path

"""
============================
  Regular continuous files
============================
"""
colour_eq_csv = join(continuous_path, 'XP_CONTINUOUS_RAW_colour_eq_dr3int6.csv')

"""
==================
  Solution files
==================
"""
colour_eq_path = join(files_path, 'colour_equation')
johnson_solution_path = join(colour_eq_path, 'Landolt_Johnson_Ucorr_v375wiv142r_SAMPLE.csv')
johnson_solution_df = pd.read_csv(johnson_solution_path)
