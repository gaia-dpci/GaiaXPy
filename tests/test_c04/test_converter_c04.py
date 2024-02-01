from os.path import join

import numpy as np
import pandas as pd
import pandas.testing as pdt

from gaiaxpy.config.paths import spline_bases_file
from gaiaxpy.converter.converter import _convert
from gaiaxpy.core.generic_functions import str_to_array
from tests.files.paths import files_path


def test_missing_band_source():
    test_files_path = join(files_path, 'xp_continuous_c04')
    input_file = join(test_files_path, 'regular_single_source.avro')
    output_file = join(test_files_path, 'regular_single_source_converter_c04.csv')
    solution_df = pd.read_csv(output_file, float_precision='round_trip', converters={'flux': lambda x: str_to_array(x),
                                                                               'flux_error': lambda x: str_to_array(x)})
    output_df, _ = _convert(input_file, save_file=False, config_file=spline_bases_file)
    pdt.assert_frame_equal(output_df, solution_df)

def test_missing_band_source_with_correlation():
    test_files_path = join(files_path, 'xp_continuous_c04')
    input_file = join(test_files_path, 'regular_single_source.avro')
    output_file = join(test_files_path, 'regular_single_source_converter_c04_with_corr.csv')
    solution_df = pd.read_csv(output_file, float_precision='round_trip', converters={key: lambda x: str_to_array(x)
                                                                                     for key in ['correlation', 'flux',
                                                                                                 'flux_error']})
    output_df, _ = _convert(input_file, sampling=np.linspace(0.0, 60.0, 18), save_file=False,
                                   config_file=spline_bases_file, with_correlation=True)
    pdt.assert_frame_equal(output_df, solution_df)
    