import warnings
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from astroquery import log
from astroquery.utils.tap.conn.tapconn import TapConn
from requests.exceptions import ConnectionError, HTTPError, Timeout

from gaiaxpy import convert
from gaiaxpy.core.custom_errors import ArchiveAuthenticationError
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.input_reader.archive_output import import_gaia_class
from gaiaxpy.input_reader.archive_reader import ArchiveReader
from gaiaxpy.input_reader.list_reader import IterableReader
from gaiaxpy.input_reader.query_reader import QueryReader


def response(status=200, cookie=True):
    return SimpleNamespace(status=status, reason='Test response', close=Mock(),
                           read=Mock(side_effect=AssertionError('Do not read an HTML error body')),
                           getheaders=lambda: [('Set-Cookie', 'SESSION=test; Path=/')] if cookie else [])


@pytest.fixture
def astroquery_client(mocker):
    # Astroquery creates a default client on first import; stub its notification
    # request as well as both login endpoints. No network access is permitted.
    mocker.patch('http.client.HTTPConnection.connect', side_effect=AssertionError('Unexpected network access'))
    mocker.patch.object(TapConn, 'execute_tapget', return_value=SimpleNamespace(status=200))
    client = import_gaia_class()(show_server_messages=False)
    tap = client._Tap__connHandler
    data = client._GaiaClass__gaiadata._Tap__connHandler
    mocker.patch.object(tap, 'execute_secure', return_value=response())
    mocker.patch.object(data, 'execute_secure', return_value=response())
    return client, tap, data


def reader(quiet=True, credentials_file=None):
    return ArchiveReader(convert, False, None if credentials_file else 'user',
                         None if credentials_file else 'wrong-secret', credentials_file=credentials_file,
                         release=RELEASES.dr3, disable_info=quiet)


@pytest.mark.parametrize('quiet', [False, True])
@pytest.mark.parametrize('service', ['tap', 'data'])
@pytest.mark.parametrize('status,expected', [(401, 'rejected the supplied credentials'), (403, 'denied access')])
def test_real_astroquery_authentication_failure_is_concise_and_connections_are_restored(
        astroquery_client, quiet, service, status, expected, capsys):
    client, tap, data = astroquery_client
    failed_connection = tap if service == 'tap' else data
    failed_response = response(status)
    failed_connection.execute_secure.return_value = failed_response
    originals = [connection.check_launch_response_status for connection in (tap, data)]
    filters = list(log.filters)
    with log.log_to_list() as records:
        with pytest.raises(ArchiveAuthenticationError) as error:
            reader(quiet)._login(client)
    text = str(error.value)
    assert expected in text
    assert f'HTTP {status}' in text
    assert 'credentials_file' not in text
    assert 'interactive' not in text
    assert 'wrong-secret' not in text
    assert error.value.__suppress_context__
    printed = capsys.readouterr()
    assert '<html' not in printed.out + printed.err
    assert 'Error logging in' not in printed.out + printed.err
    assert not any(record.getMessage().startswith('Error logging in') for record in records)
    if quiet:
        assert printed.out == printed.err == ''
    assert log.filters == filters
    assert [connection.check_launch_response_status for connection in (tap, data)] == originals
    assert all('check_launch_response_status' not in vars(connection) for connection in (tap, data))
    failed_response.close.assert_called_once()
    failed_response.read.assert_not_called()
    if service == 'tap':
        data.execute_secure.assert_not_called()
    else:
        # GaiaClass still logs out of TAP after its data-service login fails.
        assert tap.execute_secure.call_count == 2
        assert tap.execute_secure.call_args.args[0] == 'logout'
        assert not client._TapPlus__isLoggedIn


@pytest.mark.parametrize('status', [429, 500, 503])
@pytest.mark.parametrize('service', ['tap', 'data'])
def test_swallowed_service_http_errors_keep_their_status(astroquery_client, status, service, capsys):
    client, tap, data = astroquery_client
    (tap if service == 'tap' else data).execute_secure.return_value = response(status)
    with pytest.raises(HTTPError) as error:
        reader()._login(client)
    assert error.value.response.status_code == status
    assert 'wrong-secret' not in str(error.value)
    assert 'username and password' not in str(error.value)
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize('exception', [ConnectionError('Connection failed'), Timeout('Timed out')])
def test_network_errors_propagate_and_restore_response_checks(astroquery_client, exception):
    client, tap, data = astroquery_client
    tap.execute_secure.side_effect = exception
    originals = [connection.check_launch_response_status for connection in (tap, data)]
    with pytest.raises(type(exception)) as error:
        reader()._login(client)
    assert error.value is exception
    assert [connection.check_launch_response_status for connection in (tap, data)] == originals


@pytest.mark.parametrize('quiet', [False, True])
def test_successful_login_preserves_diagnostics_and_response_checks(astroquery_client, quiet):
    client, tap, data = astroquery_client
    original = data.execute_secure.return_value

    def login(**kwargs):
        warnings.warn('Important login warning', UserWarning)
        log.warning('Archive warning')
        log.error('Separate diagnostic')
        return original

    data.execute_secure.side_effect = login
    with log.log_to_list() as records:
        with pytest.warns(UserWarning, match='Important login warning'):
            reader(quiet)._login(client)
    messages = [record.getMessage() for record in records]
    assert 'Archive warning' in messages
    assert 'Separate diagnostic' in messages
    assert ('Login to gaia TAP server' in messages) is not quiet
    assert client._TapPlus__isLoggedIn
    assert client._GaiaClass__gaiadata._TapPlus__isLoggedIn


def test_failure_keeps_unrelated_warnings_and_errors(astroquery_client):
    client, tap, data = astroquery_client
    bad = response(401)
    tap.execute_secure.return_value = bad

    # Emit diagnostics when the failing response is closed, after it was recorded.
    def close():
        warnings.warn('Important response warning', UserWarning)
        log.warning('Keep this warning')
        log.error('Keep this error')

    bad.close.side_effect = close
    with log.log_to_list() as records:
        with pytest.warns(UserWarning, match='Important response warning'):
            with pytest.raises(ArchiveAuthenticationError):
                reader()._login(client)
    assert [record.getMessage() for record in records] == ['Keep this warning', 'Keep this error']


def test_no_session_cookie_uses_generic_failure_without_claiming_http_status(astroquery_client):
    client, tap, data = astroquery_client
    data.execute_secure.return_value = response(cookie=False)
    with pytest.raises(ArchiveAuthenticationError) as error:
        reader()._login(client)
    assert 'authentication did not complete' in str(error.value)
    assert 'HTTP' not in str(error.value)
    assert 'credentials_file' not in str(error.value)


def test_existing_instance_response_checker_is_restored(astroquery_client, mocker):
    client, tap, data = astroquery_client
    original = mocker.patch.object(tap, 'check_launch_response_status', wraps=tap.check_launch_response_status)
    tap.execute_secure.return_value = response(401)
    with pytest.raises(ArchiveAuthenticationError):
        reader()._login(client)
    assert tap.check_launch_response_status is original


def test_wrong_file_credentials_do_not_trigger_another_prompt(astroquery_client, tmp_path, mocker):
    client, tap, data = astroquery_client
    tap.execute_secure.return_value = response(401)
    path = tmp_path / 'credentials.txt'
    path.write_text('user\nwrong-secret\n')
    mocker.patch('builtins.input', side_effect=AssertionError('Unexpected retry'))
    mocker.patch('getpass.getpass', side_effect=AssertionError('Unexpected retry'))
    with pytest.raises(ArchiveAuthenticationError, match='HTTP 401'):
        reader(credentials_file=path)._login(client)


@pytest.mark.parametrize('query', [False, True])
def test_login_failure_stops_list_and_query_retrieval(astroquery_client, mocker, query):
    client, tap, data = astroquery_client
    tap.execute_secure.return_value = response(401)
    mocker.patch('gaiaxpy.input_reader.archive_reader.import_gaia_class', return_value=lambda **kwargs: client)
    query_request = mocker.patch.object(client, 'launch_job_async')
    download = mocker.patch.object(client, 'load_data')
    archive = (QueryReader('select source_id from example', convert, False, user='user',
                           password='wrong-secret',
                           release=RELEASES.dr3, disable_info=True) if query else
               IterableReader([123], convert, False, 'user', 'wrong-secret',
                              release=RELEASES.dr3, disable_info=True))
    with pytest.raises(ArchiveAuthenticationError, match='HTTP 401'):
        archive.read()
    query_request.assert_not_called()
    download.assert_not_called()
