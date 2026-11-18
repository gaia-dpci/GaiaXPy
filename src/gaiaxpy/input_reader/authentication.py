"""Validate Cosmos credentials and verify Gaia Archive authentication."""

import builtins
import getpass
import sys
import warnings
from pathlib import Path

from gaiaxpy.core.custom_errors import ArchiveAuthenticationError


def _can_prompt():
    """Return whether terminal or notebook input is available for login.

    Notebook kernels must explicitly allow stdin. Other sessions require a
    terminal attached to standard input.
    """
    get_shell = getattr(builtins, 'get_ipython', None)
    shell = get_shell() if callable(get_shell) else None
    kernel = getattr(shell, 'kernel', None)
    if kernel is not None:
        # Notebook runners such as nbconvert may expose a kernel but disallow input.
        return getattr(kernel, '_allow_stdin', False) is True
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except (AttributeError, OSError, ValueError):
        return False


def _validate_credentials_file(credentials_file):
    """Check a UTF-8 file containing a username and password on separate lines.

    Args:
        credentials_file (str or pathlib.Path): Credentials filename.

    Returns:
        str: Expanded filename, after validating two non-empty credential lines.
        Additional whitespace-only content is allowed.

    Raises:
        ValueError: The file is not UTF-8 text or its credential layout is invalid.

    Notes:
        File access errors keep their original exception types. The file is read
        for validation and is not modified.
    """
    path = Path(credentials_file).expanduser()
    try:
        with path.open(encoding='utf-8') as stream:
            username = stream.readline().strip()
            password = stream.readline().strip()
            extra = stream.read().strip()
    except UnicodeError:
        raise ValueError('Credentials file must be UTF-8 text containing a Cosmos username '
                         'and password on separate lines.') from None
    # FileNotFoundError, PermissionError and other file errors retain their own types.
    if not username or not password or extra:
        raise ValueError('Credentials file must only contain a Cosmos username on the first line '
                         'and a password on the second line.')
    return str(path)


def prepare_login_arguments(user, password, credentials_file, release):
    """Validate credentials and obtain missing login details when needed.

    Args:
        user (str or None): Cosmos username.
        password (str or None): Cosmos password; requires user.
        credentials_file (str or pathlib.Path or None): Two-line credentials
            file, used instead of user and password.
        release (str): Release used to determine whether login is required.

    Returns:
        dict: Arguments for GaiaClass.login, or an empty dictionary for anonymous
        access when no username is supplied and the release is not restricted.

    Raises:
        ValueError: Credential options conflict, a supplied username or password
            is invalid, or the credentials file has an invalid layout.
        ArchiveAuthenticationError: Login needs interactive input that is
            unavailable, hidden password entry is unavailable, or entry is
            cancelled or empty.

    Notes:
        A missing password is requested interactively when possible. No
        server is contacted here.
    """
    if credentials_file is not None and (user is not None or password is not None):
        raise ValueError('credentials_file cannot be used together with username or password.')
    if credentials_file is not None:
        return {'credentials_file': _validate_credentials_file(credentials_file)}
    if password is not None and user is None:
        raise ValueError('A password was supplied without a username. Supply username as well, '
                         'or omit both to sign in interactively.')
    if user is not None and (not isinstance(user, str) or not user.strip()):
        raise ValueError('Cosmos username must be a non-empty string.')
    if password is not None and (not isinstance(password, str) or not password.strip()):
        raise ValueError('Cosmos password must be a non-empty string.')
    if user is None:
        return {}  # Preserve anonymous access to public DR3 data.
    if password is not None:
        return {'user': user, 'password': password}
    if not _can_prompt():
        raise ArchiveAuthenticationError(release, reason='Interactive login is unavailable in this session.')

    print('Please enter your Cosmos password to sign in to the Gaia Archive.')
    try:
        if user is None:
            user = input('Cosmos username: ').strip()
            if not user:
                raise ArchiveAuthenticationError(release, reason='Login cancelled: no username was entered.')
        # getpass otherwise falls back to visible input if hidden input is unavailable.
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            password = getpass.getpass('Cosmos password: ')
        if not password or not password.strip():
            raise ArchiveAuthenticationError(release, reason='Login cancelled: no password was entered.')
    except (EOFError, KeyboardInterrupt):
        raise ArchiveAuthenticationError(release,
                                         reason='Archive login was cancelled or input was unavailable.') from None
    except getpass.GetPassWarning:
        raise ArchiveAuthenticationError(release,
                                         reason='Hidden password input is unavailable in this session.') from None
    return {'user': user, 'password': password}


def verify_login(gaia, release):
    """Require successful authentication to both TAP and data services.

    Args:
        gaia (astroquery.gaia.GaiaClass): Client whose login was attempted.
        release (str): Release included in an authentication error.

    Raises:
        ArchiveAuthenticationError: Either service is not authenticated.

    Notes:
        Astroquery may report a failed login without raising an exception.
        This check uses its stored service state to detect that case.
    """
    # Astroquery currently exposes no public authentication-status accessor.
    # Keep its state details here rather than spreading them across the readers.
    data_service = getattr(gaia, '_GaiaClass__gaiadata', None)
    tap_ok = getattr(gaia, '_TapPlus__isLoggedIn', False) is True
    data_ok = getattr(data_service, '_TapPlus__isLoggedIn', False) is True
    if not (tap_ok and data_ok):
        raise ArchiveAuthenticationError(release,
                                         reason='Archive authentication did not complete. Check your credentials, '
                                                'account access and Archive availability. No data were retrieved.',
                                         include_guidance=False)


def login_error(release, status=None):
    """Build an authentication exception describing the failed login.

    Args:
        release (str): Gaia release associated with the login attempt.
        status (int or None): HTTP status, when known. Statuses 401 and 403
            receive credential and permission guidance respectively.

    Returns:
        ArchiveAuthenticationError: Exception for the caller to raise. This
        helper does not raise it itself.
    """
    if status == 401:
        reason = ('The Gaia Archive rejected the supplied credentials (HTTP 401). '
                  'Check your Cosmos username and password.')
    elif status == 403:
        reason = ('The Gaia Archive denied access (HTTP 403). Check that your Cosmos account '
                  'has permission to access this Archive.')
    else:
        reason = ('The Archive login request failed. Check your credentials, account access '
                  'and Archive availability.')
    return ArchiveAuthenticationError(release, reason=reason, include_guidance=False)
