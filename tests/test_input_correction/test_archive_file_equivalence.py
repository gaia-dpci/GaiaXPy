from unittest.mock import Mock

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest
from astropy.table import Table

from gaiaxpy import calibrate, convert, generate, PhotometricSystem
from gaiaxpy.core.custom_errors import InvalidReleaseError
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.continuous import dr3_with_missing_bp_csv_file


@pytest.fixture(params=list(RELEASES))
def equivalent_inputs(request, tmp_path, mocker):
    release = request.param
    if release == RELEASES.dr3:
        raw = pd.read_csv(dr3_with_missing_bp_csv_file, **CSV_FLOAT_PRECISION_KWARGS)
    else:
        raise InvalidReleaseError(release)
    path = tmp_path / 'spectra.csv'
    raw.to_csv(path, index=False)

    client = Mock()
    result_key = 'XP_CONTINUOUS-example.csv' if release == RELEASES.dr3 else 'MEAN_SPECTRUM_XP-example.csv'
    client.load_data.return_value = {result_key: [Table.from_pandas(raw)]}
    client.launch_job_async.return_value.get_results.return_value = Table({'source_id': raw['source_id'].tolist()})
    mocker.patch('gaiaxpy.input_reader.archive_reader.ArchiveReader._get_archive_client', return_value=client)
    return release, raw, path, client


def archive_input(kind, raw):
    if kind == 'ids':
        return raw['source_id'].tolist()
    return 'SELECT source_id FROM example'


@pytest.mark.parametrize('kind', ['ids', 'query'])
@pytest.mark.parametrize('enabled', [False, True], ids=['uncorrected', 'corrected'])
@pytest.mark.parametrize('truncation', [False, True], ids=['all-bases', 'truncated'])
def test_readers_produce_identical_coefficients_and_covariances(
        equivalent_inputs, mocker, kind, enabled, truncation):
    release, raw, path, client = equivalent_inputs
    readers = [InputReader(content, convert, truncation=truncation, disable_info=True, release=release)
               for content in (path, archive_input(kind, raw))]
    expected, actual = [reader.read() for reader in readers]

    # FileReader uses NumPy scalar dtypes; DataFrameReader retains nullable
    # pandas dtypes. Compare numerical values exactly across those containers.
    pdt.assert_frame_equal(actual[0], expected[0], check_exact=True, check_like=True, check_dtype=False)
    assert actual[1:] == expected[1:] == ('csv', release)
    client.load_data.assert_called_once()
    assert client.launch_job_async.call_count == (1 if kind == 'query' else 0)


@pytest.mark.parametrize('kind', ['ids', 'query'])
@pytest.mark.parametrize('enabled', [False, True], ids=['uncorrected', 'corrected'])
@pytest.mark.parametrize('function', [calibrate, convert, generate], ids=lambda function: function.__name__)
def test_public_results_match_for_file_and_archive(equivalent_inputs, kind, enabled, function):
    release, raw, path, _ = equivalent_inputs
    options = dict(release=release, save_file=False, disable_info=True)
    if function is generate and release == RELEASES.dr3:
        options['photometric_system'] = PhotometricSystem.DR3_Gaia_Vega
    expected = function(path, **options)
    actual = function(archive_input(kind, raw), **options)
    if function is generate:
        pdt.assert_frame_equal(actual, expected, check_exact=True, check_dtype=False)
    else:
        pdt.assert_frame_equal(actual[0], expected[0], check_exact=True)
        np.testing.assert_array_equal(actual[1], expected[1])
