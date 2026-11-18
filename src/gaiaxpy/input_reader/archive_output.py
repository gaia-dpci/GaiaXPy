"""Control routine Archive messages without suppressing warnings and errors."""

import logging
from contextlib import contextmanager, redirect_stdout
from contextvars import ContextVar
from io import StringIO

from astroquery import log

_quiet = ContextVar('gaiaxpy_quiet_archive', default=False)


class _RoutineOutputFilter(logging.Filter):
    """Filter routine Astroquery log records in the active quiet context."""

    def filter(self, record):
        """Keep warnings and errors, and keep other records outside quiet contexts."""
        return record.levelno >= logging.WARNING or not _quiet.get()


@contextmanager
def archive_output(disable_info):
    """Temporarily filter routine Astroquery log records when requested.

    Args:
        disable_info (bool): Filter records below WARNING while the context is
            active. False leaves logging unchanged.

    Yields:
        None: The caller's Archive operation runs inside this context.

    Notes:
        The filter and context state are restored even if the operation fails.
        This does not redirect printed output or silence authentication prompts.
    """
    if not disable_info:
        yield
        return
    token = _quiet.set(True)
    output_filter = _RoutineOutputFilter()
    log.addFilter(output_filter)
    try:
        yield
    finally:
        log.removeFilter(output_filter)
        _quiet.reset(token)


def import_gaia_class():
    """Import GaiaClass without its default client's stdout announcement.

    Returns:
        type: Astroquery's GaiaClass, used to create a release-specific client.

    Notes:
        Only stdout during the lazy import is redirected. Warnings and errors
        on stderr remain visible; login and retrieval output are not captured.
    """
    with redirect_stdout(StringIO()):
        from astroquery.gaia import GaiaClass
    return GaiaClass
