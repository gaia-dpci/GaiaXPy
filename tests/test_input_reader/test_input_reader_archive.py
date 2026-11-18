import pandas.testing as pdt
import pytest

from gaiaxpy import calibrate
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.continuous import dr3_mean_spectra_csv_file

_rtol, _atol = 1e-24, 1e-24


@pytest.mark.archive
def test_path_vs_query():
    # Calibrator requires use of internal calibrate function
    dr3 = RELEASES.dr3
    query_input = "SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816', '5853498713190525696')"
    parsed_data_file, _, _ = InputReader(dr3_mean_spectra_csv_file, calibrate, truncation=False, release=dr3).read()
    parsed_data_query, _, _ = InputReader(query_input, calibrate, truncation=False, release=dr3).read()
    # The Archive will return all columns, not only the ones required by the tools
    parsed_data_query = parsed_data_query[parsed_data_file.columns]
    # Windows version will return different dtypes
    parsed_data_query = parsed_data_query.astype({'source_id': 'int64'})
    pdt.assert_frame_equal(parsed_data_file.sort_values('source_id', ignore_index=True),
                           parsed_data_query.sort_values('source_id', ignore_index=True),
                           rtol=_rtol, atol=_atol, check_dtype=False)
