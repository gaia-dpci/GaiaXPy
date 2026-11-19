from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from astropy.table import Table

from gaiaxpy import calibrate, convert, generate
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.input_reader.archive_reader import ArchiveReader
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.list_reader import IterableReader
from gaiaxpy.input_reader.query_reader import QueryReader
from gaiaxpy.input_reader.source_ids import validate_source_ids


@pytest.mark.parametrize('sources', [[1, np.int64(2019517403836492416)], (np.uint64(2), 1, 2)])
def test_integer_ids_preserve_precision_order_and_duplicates(sources):
    actual = validate_source_ids(sources)
    assert actual == list(sources)
    assert all(isinstance(source, (int, np.integer)) for source in actual)


@pytest.mark.parametrize('sources,expected', [
    (['9007199254740993', '2019517403836492416'], [9007199254740993, 2019517403836492416]),
    (('123', np.int64(7), '123'), [123, 7, 123]),
    (['  +00123  ', '-2'], [123, -2]),
    (np.array(['9007199254740993', '7']), [9007199254740993, 7]),
    (np.array(['123', np.uint64(7), '123'], dtype=object), [123, 7, 123]),
    (np.array([np.uint64(2 ** 63), np.uint64(7)]), [2 ** 63, 7]),
    (np.ma.array(['123', '7'], mask=False), [123, 7]),
])
def test_string_and_mixed_ids_are_normalised_without_precision_loss(sources, expected):
    original = sources.copy() if isinstance(sources, np.ndarray) else list(sources)
    actual = validate_source_ids(sources)
    assert actual == expected
    assert all(type(source) is int for source in actual)
    if isinstance(sources, np.ndarray):
        np.testing.assert_array_equal(sources, original)
    else:
        assert list(sources) == original


@pytest.mark.parametrize('bad', ['', ' ', '1.0', '1e3', '1_000', '1 2', '+', 'abc', b'123',
                                 "1); DROP TABLE stars;--", 1.0, np.float64(1),
                                 True, np.bool_(False), None, np.nan])
@pytest.mark.parametrize('function', [convert])
def test_invalid_ids_fail_before_archive_connection(mocker, bad, function):
    connect = mocker.patch.object(ArchiveReader, '_get_archive_client',
                                  side_effect=AssertionError('Unexpected Archive connection'))
    with pytest.raises(TypeError, match='must contain only integers'):
        InputReader([123, bad], function, truncation=False, release=RELEASES.dr3).read()
    connect.assert_not_called()


def test_empty_ids_fail_before_archive_connection(mocker):
    connect = mocker.patch.object(ArchiveReader, '_get_archive_client')
    with pytest.raises(ValueError, match='cannot be empty'):
        IterableReader([], convert, False, None, None, release=RELEASES.dr3)
    connect.assert_not_called()


@pytest.mark.parametrize('sources', ['123', b'123', np.array([['123']]),
                                     np.array([1., 2.]), np.ma.array(['123'], mask=[True])])
def test_invalid_selection_forms_are_rejected(sources):
    with pytest.raises(TypeError):
        validate_source_ids(sources)


@pytest.mark.parametrize('function', [calibrate, convert, generate])
@pytest.mark.parametrize('sources', [['9007199254740993', '7'],
                                     ('9007199254740993', np.int64(7))])
def test_string_selections_reach_archive_as_integers(mocker, function, sources):
    client = Mock()
    mocker.patch.object(ArchiveReader, '_get_archive_client', return_value=client)
    data = pd.DataFrame({'source_id': [9007199254740993, 7]})
    mocker.patch.object(ArchiveReader, '_get_result_data', return_value=data)
    reader = mocker.patch('gaiaxpy.input_reader.list_reader.DataFrameReader')
    reader.return_value.read.return_value = (data, None)
    InputReader(sources, function, truncation=False, release=RELEASES.dr3).read()
    assert client.load_data.call_args.kwargs['ids'] == [9007199254740993, 7]


def test_query_result_ids_are_validated_before_datalink(mocker):
    client = Mock()
    client.launch_job_async.return_value.get_results.return_value = Table({'source_id': ['not-an-id']})
    mocker.patch.object(ArchiveReader, '_get_archive_client', return_value=client)
    with pytest.raises(TypeError, match='must contain only integers'):
        QueryReader('SELECT source_id FROM user_table', convert, False, release=RELEASES.dr3).read()
    client.load_data.assert_not_called()


def test_query_result_string_ids_reach_datalink_as_integers(mocker):
    client = Mock()
    expected = [9007199254740993, 7]
    client.launch_job_async.return_value.get_results.return_value = Table(
        {'source_id': ['9007199254740993', '7']})
    mocker.patch.object(ArchiveReader, '_get_archive_client', return_value=client)
    data = pd.DataFrame({'source_id': expected})
    mocker.patch.object(ArchiveReader, '_get_result_data', return_value=data)
    mocker.patch('gaiaxpy.input_reader.query_reader.DataFrameReader').return_value.read.return_value = (data, None)
    QueryReader('SELECT source_id FROM user_table', convert, False, release=RELEASES.dr3,
                disable_info=True).read()
    assert client.load_data.call_args.kwargs['ids'] == expected


def test_adql_uses_marker_without_rewriting_query(mocker):
    query = "select source_id from gaiadr3.gaia_source where designation = 'selection--test'"
    client = Mock()
    client.launch_job_async.side_effect = RuntimeError('Stop before retrieval')
    mocker.patch.object(ArchiveReader, '_get_archive_client', return_value=client)
    with pytest.raises(RuntimeError, match='Stop before retrieval'):
        calibrate(query, save_file=False)
    submitted = client.launch_job_async.call_args.args[0]
    marker, original = submitted.split('\n', 1)
    assert marker.startswith('--This query was launched from within GaiaXPy ')
    assert original == query
