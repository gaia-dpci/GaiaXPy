import numpy as np
import pandas as pd
import pandas.testing as pdt
from gaiaxpy.config.paths import spline_bases_file
from gaiaxpy.converter.converter import _convert
from gaiaxpy.core.generic_functions import str_to_array

from tests.test_c04.c04_paths import regular_single_source_file, no_corr_output_file, with_corr_output_file


def test_missing_band_source():
    solution_df = pd.read_csv(no_corr_output_file, float_precision='round_trip',
                              converters={'flux': lambda x: str_to_array(x), 'flux_error': lambda x: str_to_array(x)})
    output_df, _ = _convert(regular_single_source_file, config_file=spline_bases_file, save_file=False)
    pdt.assert_frame_equal(output_df, solution_df)


def test_missing_band_source_with_correlation():
    solution_df = pd.read_csv(with_corr_output_file, float_precision='round_trip',
                              converters={key: lambda x: str_to_array(x) for key in ['correlation', 'flux',
                                                                                     'flux_error']})
    output_df, _ = _convert(regular_single_source_file, sampling=np.linspace(0.0, 60.0, 18),
                            config_file=spline_bases_file, with_correlation=True, save_file=False)
    pdt.assert_frame_equal(output_df, solution_df)
