import pytest

from gaiaxpy import generate
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.continuous import (dr3_mean_spectra_avro_file, dr3_mean_spectra_csv_file, dr3_mean_spectra_ecsv_file,
                                    dr3_mean_spectra_fits_file, dr3_mean_spectra_xml_binary_file,
                                    dr3_mean_spectra_xml_plain_file)
from tests.utils.utils import assert_dfs_equal

input_files = [dr3_mean_spectra_avro_file, dr3_mean_spectra_csv_file, dr3_mean_spectra_ecsv_file,
               dr3_mean_spectra_fits_file, dr3_mean_spectra_xml_binary_file, dr3_mean_spectra_xml_plain_file]


@pytest.mark.parametrize("input_file", input_files)
def test_input_correction_dr3(input_file):
    """Input correction does not apply for DR3 data"""
    with_correction, _, _ = InputReader(input_file, generate, truncation=False, release='dr3').read()
    without_correction, _, _ = InputReader(input_file, generate, truncation=False, release='dr3').read()
    assert_dfs_equal(with_correction, without_correction, rtol=0, atol=1e-30)
