import unittest
import pandas as pd
import pandas.testing as pdt

from gaiaxpy import generate, PhotometricSystem
from tests.files.paths import with_missing_bp_csv_file, no_correction_solution_path


class TestAddColDFGenerate(unittest.TestCase):

    def test_one_non_required_add_col_as_list(self):
        df = pd.read_csv(with_missing_bp_csv_file)
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