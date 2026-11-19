import builtins
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest
from requests.exceptions import ConnectionError, HTTPError, Timeout

from gaiaxpy import convert
from gaiaxpy.core.custom_errors import ArchiveAuthenticationError
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.input_reader.archive_reader import ArchiveReader
from gaiaxpy.input_reader.authentication import _can_prompt, verify_login
from gaiaxpy.input_reader.list_reader import IterableReader
from gaiaxpy.input_reader.query_reader import QueryReader


def reader(release=RELEASES.dr3, user=None, password=None, credentials_file=None, disable_info=True):
    return ArchiveReader(convert, False, user, password, release=release,
                         credentials_file=credentials_file, disable_info=disable_info)


def gaia_client(tap=True, data=True):
    client = Mock()
    client._TapPlus__isLoggedIn = tap
    client._GaiaClass__gaiadata._TapPlus__isLoggedIn = data
    return client


@pytest.fixture
def no_prompt(mocker):
    mocker.patch('gaiaxpy.input_reader.authentication._can_prompt', return_value=False)
    username = mocker.patch('builtins.input', side_effect=AssertionError('Unexpected username prompt'))
    password = mocker.patch('gaiaxpy.input_reader.authentication.getpass.getpass',
                            side_effect=AssertionError('Unexpected password prompt'))
    return username, password


@pytest.fixture
def interactive(mocker):
    mocker.patch('gaiaxpy.input_reader.authentication._can_prompt', return_value=True)
    username = mocker.patch('builtins.input', return_value='example-user')
    password = mocker.patch('gaiaxpy.input_reader.authentication.getpass.getpass', return_value='example-secret')
    return username, password


@pytest.fixture
def astroquery_mock(mocker):
    module = ModuleType('astroquery.gaia')
    module.GaiaClass = Mock(return_value=gaia_client())
    mocker.patch.dict(sys.modules, {'astroquery.gaia': module})
    return module.GaiaClass


def test_username_only_prompts_for_password(interactive):
    username, password = interactive
    client = gaia_client()
    reader(user='supplied-user')._login(client)
    username.assert_not_called()
    password.assert_called_once()
    client.login.assert_called_once_with(user='supplied-user', password='example-secret')


@pytest.mark.parametrize('release', [RELEASES.dr3, ])
def test_explicit_credentials_never_prompt(release, no_prompt):
    client = gaia_client()
    reader(release, 'user', 'secret')._login(client)
    client.login.assert_called_once_with(user='user', password='secret')


def test_dr3_remains_anonymous_without_credentials(no_prompt):
    client = gaia_client(tap=False, data=False)
    reader(RELEASES.dr3)._login(client)
    client.login.assert_not_called()


@pytest.mark.parametrize('user,password', [(None, 'secret'), ('', None), ('  ', None), (3, 'secret'),
                                           ('user', ''), ('user', 42)])
def test_invalid_explicit_credentials_fail_before_client_creation(user, password, no_prompt, astroquery_mock):
    with pytest.raises(ValueError):
        reader(user=user, password=password)._get_archive_client()
    astroquery_mock.assert_not_called()


@pytest.mark.parametrize('user,password', [('user', None), (None, 'secret'), ('user', 'secret'), ('', None)])
def test_file_and_explicit_credentials_are_mutually_exclusive(user, password, no_prompt, astroquery_mock):
    with pytest.raises(ValueError, match='cannot be used together'):
        reader(user=user, password=password, credentials_file='missing.txt')._get_archive_client()
    astroquery_mock.assert_not_called()


@pytest.mark.parametrize('release', [RELEASES.dr3, ])
def test_credentials_file_with_spaces_is_validated_and_passed_to_astroquery(tmp_path, release, no_prompt):
    path = tmp_path / 'credentials file.txt'
    path.write_text('user\nsecret\n', encoding='utf-8')
    client = gaia_client()
    reader(release, credentials_file=path)._login(client)
    client.login.assert_called_once_with(credentials_file=str(path))


@pytest.mark.parametrize('contents', ['', 'user\n', '\nsecret\n', 'user\n\n', 'user\nsecret\nextra-secret\n'])
def test_malformed_files_fail_before_client_creation_without_exposing_contents(tmp_path, contents, no_prompt,
                                                                               astroquery_mock):
    path = tmp_path / 'credentials.txt'
    path.write_text(contents)
    with pytest.raises(ValueError, match='first line.*second line') as error:
        reader(credentials_file=path)._get_archive_client()
    assert 'extra-secret' not in str(error.value)
    astroquery_mock.assert_not_called()


def test_missing_file_remains_a_file_error(tmp_path, no_prompt, astroquery_mock):
    with pytest.raises(FileNotFoundError):
        reader(credentials_file=tmp_path / 'missing.txt')._get_archive_client()
    astroquery_mock.assert_not_called()


def test_unreadable_file_remains_a_permission_error(tmp_path, mocker, no_prompt, astroquery_mock):
    mocker.patch.object(Path, 'open', side_effect=PermissionError('Cannot read credentials file'))
    with pytest.raises(PermissionError):
        reader(credentials_file=tmp_path / 'credentials.txt')._get_archive_client()
    astroquery_mock.assert_not_called()


def test_non_text_credentials_file_is_rejected(tmp_path, no_prompt, astroquery_mock):
    path = tmp_path / 'credentials.txt'
    path.write_bytes(b'\xff\xfe')
    with pytest.raises(ValueError, match='UTF-8 text'):
        reader(credentials_file=path)._get_archive_client()
    astroquery_mock.assert_not_called()


@pytest.mark.parametrize('tap,data', [(False, False), (True, False), (False, True)])
def test_swallowed_login_failure_stops_both_readers_before_retrieval(astroquery_mock, no_prompt, tap, data):
    client = gaia_client(tap=tap, data=data)
    astroquery_mock.return_value = client
    for archive in [IterableReader([123], convert, False, 'user', 'secret', release=RELEASES.dr3),
                    QueryReader('select source_id from example', convert, False,
                                user='user', password='secret', release=RELEASES.dr3)]:
        with pytest.raises(ArchiveAuthenticationError, match='authentication did not complete') as error:
            archive.read()
        assert 'secret' not in str(error.value)
    client.launch_job_async.assert_not_called()
    client.load_data.assert_not_called()


def test_rejected_file_credentials_do_not_trigger_replacement_prompts(tmp_path, astroquery_mock, no_prompt):
    path = tmp_path / 'credentials.txt'
    path.write_text('user\nwrong-secret\n')
    astroquery_mock.return_value = gaia_client(tap=False, data=False)
    with pytest.raises(ArchiveAuthenticationError) as error:
        reader(credentials_file=path)._get_archive_client()
    assert 'wrong-secret' not in str(error.value)


@pytest.mark.parametrize('status', [401, 403])
def test_raised_authentication_http_errors_are_explained_without_echoing_secrets(status, no_prompt):
    client = gaia_client()
    client.login.side_effect = HTTPError('upstream secret', response=SimpleNamespace(status_code=status))
    with pytest.raises(ArchiveAuthenticationError) as error:
        reader(user='user', password='secret')._login(client)
    assert 'secret' not in str(error.value)
    assert error.value.__suppress_context__


@pytest.mark.parametrize('exception', [ConnectionError('offline'), Timeout('timeout'),
                                       HTTPError('service unavailable', response=SimpleNamespace(status_code=503))])
def test_network_and_raised_service_errors_are_not_relabelled_as_wrong_passwords(exception, no_prompt):
    client = gaia_client()
    client.login.side_effect = exception
    with pytest.raises(type(exception)) as error:
        reader(user='user', password='secret')._login(client)
    assert error.value is exception


@pytest.mark.parametrize('tty', [False, True])
def test_terminal_prompt_detection(monkeypatch, tty):
    monkeypatch.delattr(builtins, 'get_ipython', raising=False)
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(isatty=lambda: tty))
    assert _can_prompt() is tty


@pytest.mark.parametrize('allow_stdin', [False, True])
def test_notebook_prompt_detection_respects_kernel_input_permission(monkeypatch, allow_stdin):
    shell = SimpleNamespace(kernel=SimpleNamespace(_allow_stdin=allow_stdin))
    monkeypatch.setattr(builtins, 'get_ipython', lambda: shell, raising=False)
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(isatty=lambda: False))
    assert _can_prompt() is allow_stdin


def test_absent_stdin_does_not_prompt(monkeypatch):
    monkeypatch.delattr(builtins, 'get_ipython', raising=False)
    monkeypatch.setattr(sys, 'stdin', None)
    assert _can_prompt() is False


@pytest.mark.parametrize('data_has_cookie', [False, True])
def test_verification_uses_actual_astroquery_authentication_state(data_has_cookie):
    from astroquery.utils.tap.core import TapPlus

    def service(has_cookie):
        connection = Mock()
        connection.check_launch_response_status.return_value = False
        connection.find_all_headers.return_value = ['SESSION=test; Path=/'] if has_cookie else []
        response = Mock(status=200)
        response.getheaders.return_value = []
        connection.execute_secure.return_value = response
        client = TapPlus(url='https://example.invalid', connhandler=connection)
        # A normal return alone does not prove that the server supplied a session cookie.
        assert client.login(user='user', password='test-secret') is None
        return client

    client = service(True)
    client._GaiaClass__gaiadata = service(data_has_cookie)
    if data_has_cookie:
        verify_login(client, RELEASES.dr3)
    else:
        with pytest.raises(ArchiveAuthenticationError, match='authentication did not complete'):
            verify_login(client, RELEASES.dr3)


@pytest.mark.parametrize('closed_error', [OSError('closed'), ValueError('closed')])
def test_unusable_stdin_does_not_prompt(monkeypatch, closed_error):
    monkeypatch.delattr(builtins, 'get_ipython', raising=False)
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(isatty=Mock(side_effect=closed_error)))
    assert _can_prompt() is False
