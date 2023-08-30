import unittest
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import generate, PhotometricSystem
from tests.files.paths import with_missing_bp_csv_file, no_correction_solution_path

df = pd.read_csv(with_missing_bp_csv_file)


class TestAddColDFGenerate(unittest.TestCase):

    def test_one_non_required_additional_col_as_list(self):
        additional_columns = ['solution_id']
        ps = PhotometricSystem.SDSS
        solution = pd.read_csv(no_correction_solution_path)
        solution = solution.drop(columns=[c for c in solution.columns if c != 'source_id' and 'Sdss_' not in c])
        output = generate(df, photometric_system=ps, additional_columns=additional_columns, error_correction=False,
                          save_file=False)
        additional_data = output[additional_columns]
        output_to_compare = output.drop(columns=additional_columns)
        pdt.assert_frame_equal(output_to_compare, solution)
        pdt.assert_frame_equal(additional_data, df[additional_columns])

    def test_more_than_one_non_required_additional_col_as_list(self):
        additional_columns = ['solution_id', 'bp_degrees_of_freedom']
        ps = PhotometricSystem.Stromgren
        solution = pd.read_csv(no_correction_solution_path)
        solution = solution.drop(columns=[c for c in solution.columns if c != 'source_id' and 'Stromgren_' not in c])
        output = generate(df, photometric_system=ps, additional_columns=additional_columns, error_correction=False,
                          save_file=False)
        additional_data = output[additional_columns]
        output_to_compare = output.drop(columns=additional_columns)
        pdt.assert_frame_equal(output_to_compare, solution)
        pdt.assert_frame_equal(additional_data, df[additional_columns])

    def test_one_required_additional_col_as_list(self):
        additional_columns = ['source_id']
        ps = PhotometricSystem.Gaia_DR3_Vega
        solution = pd.read_csv(no_correction_solution_path)
        solution = solution.drop(columns=[c for c in solution.columns if c != 'source_id' and 'GaiaDr3Vega_' not in c])
        output = generate(df, photometric_system=ps, additional_columns=additional_columns, error_correction=False,
                          save_file=False)
        additional_data = output[additional_columns]
        output_to_compare = output  # Column is already in the output, it shouldn't be dropped before the comparison
        pdt.assert_frame_equal(output_to_compare, solution)
        pdt.assert_frame_equal(additional_data, df[additional_columns])
