"""Retain Archive login HTTP failures without echoing response bodies."""

import logging
from contextlib import contextmanager
from contextvars import ContextVar

from astroquery import log
from astroquery.utils.tap.conn.tapconn import TapConn
from requests import Response
from requests.exceptions import HTTPError

_active_failure = ContextVar('gaiaxpy_login_failure', default=None)
_MISSING = object()
_DUPLICATE_ERRORS = {'Error logging in TAP server', 'Error logging in data server', 'Logging out from TAP server'}


class _LoginFailure:
    """Keep the first failed HTTP response observed during a login attempt."""

    def __init__(self):
        """Start with no recorded login error."""
        self.error = None

    def check_response(self, original):
        """Wrap a connection status check to record HTTP errors with their status.

        The wrapper closes a failed response when possible and raises HTTPError
        without including the response body. Other checks use the original method.
        """

        def check(response, debug, expected_response_status, *, raise_exception=True):
            """Check one HTTP response, recording a failure when exceptions are enabled."""
            if response.status != expected_response_status and raise_exception:
                # The original check prints the complete response body and raises
                # HTTPError without attaching its HTTP status. Keep the status.
                safe_response = Response()
                safe_response.status_code = response.status
                error = HTTPError(f'Gaia Archive login failed (HTTP {response.status}).', response=safe_response)
                if self.error is None:
                    self.error = error
                close = getattr(response, 'close', None)
                if callable(close):
                    close()
                raise error
            return original(response, debug, expected_response_status, raise_exception=raise_exception)

        return check


class _DuplicateLoginErrorFilter(logging.Filter):
    """Omit known duplicate errors after a login failure has been recorded."""

    def __init__(self, failure):
        """Associate the log filter with one login-failure record."""
        super().__init__()
        self.failure = failure

    def filter(self, record):
        # Only omit known duplicate errors. Warnings and all other diagnostics pass through.
        """Keep records except known duplicate errors for this active failure."""
        return not (_active_failure.get() is self.failure and self.failure.error is not None
                    and record.levelno == logging.ERROR and record.getMessage() in _DUPLICATE_ERRORS)


@contextmanager
def capture_login_response(gaia):
    """Capture failures on one client's TAP and data-service connections.

    Args:
        gaia (astroquery.gaia.GaiaClass): Client whose login is about to run.

    Yields:
        _LoginFailure: Record containing the first captured HTTPError, or None
        in its error attribute when no failed response was intercepted.

    Notes:
        Connection checks and the duplicate-error log filter are restored when
        the context exits, including after exceptions. Only the supplied
        client's recognised TapConn connections are wrapped.
    """
    failure = _LoginFailure()
    token = _active_failure.set(failure)
    output_filter = _DuplicateLoginErrorFilter(failure)
    replacements = []
    log.addFilter(output_filter)
    try:
        services = (gaia, getattr(gaia, '_GaiaClass__gaiadata', None))
        for service in services:
            connection = getattr(service, '_Tap__connHandler', None)
            if not isinstance(connection, TapConn) or any(connection is item[0] for item in replacements):
                continue
            name = 'check_launch_response_status'
            previous = vars(connection).get(name, _MISSING)
            original = getattr(connection, name)
            replacements.append((connection, previous))
            setattr(connection, name, failure.check_response(original))
        yield failure
    finally:
        for connection, previous in reversed(replacements):
            if previous is _MISSING:
                del connection.check_launch_response_status
            else:
                connection.check_launch_response_status = previous
        log.removeFilter(output_filter)
        _active_failure.reset(token)
