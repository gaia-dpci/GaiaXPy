from os.path import join

import pandas as pd
import pandas.testing as pdt

from gaiaxpy import convert
from gaiaxpy.core.generic_functions import str_to_array
from tests.files.paths import files_path


def test_missing_band_source():
    test_files_path = join(files_path, 'xp_continuous_c04')
    input_file = join(test_files_path, 'regular_single_source.avro')
    output_file = join(test_files_path, 'regular_single_source_converter_c04.csv')
    solution_df = pd.read_csv(output_file, float_precision='high', converters={'flux': lambda x: str_to_array(x),
                                                                               'flux_error': lambda x: str_to_array(x)})
    output_df, _ = convert(input_file, save_file=False)
    pdt.assert_frame_equal(output_df, solution_df)


def test_convert_many():
    test_files_path = join(files_path, 'xp_continuous_c04')
    input_file = join(test_files_path, 'c04_records_1000.avro')
    _, _ = convert(input_file, save_file=False)
