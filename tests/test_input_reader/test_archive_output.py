import builtins
import sys
import warnings
from threading import Thread
from types import SimpleNamespace

import pandas as pd
import pytest
from astropy.table import Table
from astroquery import log

from gaiaxpy import calibrate
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.input_reader.archive_output import archive_output, import_gaia_class
from tests.files.continuous import dr3_mean_spectra_csv_file


@pytest.mark.parametrize('quiet', [False, True])
def test_logging_keeps_warnings_and_errors_and_restores_configuration(quiet):
    level, filters, handlers = log.level, list(log.filters), list(log.handlers)
    with log.log_to_list() as records:
        with archive_output(quiet):
            log.info('Query finished.')
            log.warning('Archive warning')
            log.error('Archive error')
        log.info('After Archive call')
    messages = [record.getMessage() for record in records]
    assert ('Query finished.' in messages) is not quiet
    assert messages[-3:] == ['Archive warning', 'Archive error', 'After Archive call']
    assert log.level == level
    assert log.filters == filters
    assert log.handlers == handlers


def test_exception_restores_logging_and_leaves_python_warnings_visible():
    original_filters = list(log.filters)
    with pytest.warns(UserWarning, match='Still important'):
        with pytest.raises(RuntimeError, match='Archive failed'):
            with archive_output(True):
                warnings.warn('Still important', UserWarning)
                raise RuntimeError('Archive failed')
    assert log.filters == original_filters
    with log.log_to_list() as records:
        log.info('Visible after failure')
    assert [record.getMessage() for record in records] == ['Visible after failure']


def test_quiet_context_does_not_filter_other_threads():
    with log.log_to_list() as records:
        with archive_output(True):
            thread = Thread(target=lambda: log.info('Other thread'))
            thread.start()
            thread.join()
            log.info('Quiet thread')
    assert [record.getMessage() for record in records] == ['Other thread']


def test_nested_quiet_context_is_restored():
    with log.log_to_list() as records:
        with archive_output(True):
            with archive_output(True):
                log.info('Inner')
            log.info('Outer')
        log.info('Restored')
    assert [record.getMessage() for record in records] == ['Restored']


def test_import_hides_only_default_client_stdout(mocker, capsys):
    original_import = builtins.__import__
    expected_class = object()

    def importing(name, *args, **kwargs):
        if name == 'astroquery.gaia':
            print('Default client announcement')
            print('Import diagnostic', file=sys.stderr)
            warnings.warn('Import warning', UserWarning)
            return SimpleNamespace(GaiaClass=expected_class)
        return original_import(name, *args, **kwargs)

    mocker.patch('builtins.__import__', side_effect=importing)
    with pytest.warns(UserWarning, match='Import warning'):
        assert import_gaia_class() is expected_class
    output = capsys.readouterr()
    assert output.out == ''
    assert 'Import diagnostic' in output.err


def test_import_failure_restores_stdout(mocker):
    original_import, original_stdout = builtins.__import__, sys.stdout

    def importing(name, *args, **kwargs):
        if name == 'astroquery.gaia':
            raise ImportError('Unavailable Astroquery module')
        return original_import(name, *args, **kwargs)

    mocker.patch('builtins.__import__', side_effect=importing)
    with pytest.raises(ImportError, match='Unavailable Astroquery module'):
        import_gaia_class()
    assert sys.stdout is original_stdout


@pytest.mark.parametrize('quiet', [False, True])
@pytest.mark.parametrize('query_input', [False, True])
def test_public_archive_call_controls_announcements_and_logs(mocker, capsys, quiet, query_input):
    frame = pd.read_csv(dr3_mean_spectra_csv_file).iloc[:1]
    sources = frame.source_id.tolist()
    original_import = builtins.__import__

    class Client:
        def __init__(self, *, gaia_tap_server, gaia_data_server, show_server_messages):
            if show_server_messages:
                print('Archive announcement')

        def launch_job_async(self, query, **kwargs):
            log.info('Query finished.')
            return SimpleNamespace(get_results=self.results)

        def results(self):
            log.info('Retrieving query results')
            return Table({'source_id': sources})

        def load_data(self, **kwargs):
            log.info('DataLink progress')
            log.warning('Archive warning remains visible')
            return {'XP_CONTINUOUS-test.csv': [Table.from_pandas(frame)]}

    def importing(name, *args, **kwargs):
        if name == 'astroquery.gaia':
            print('Default client announcement')
            return SimpleNamespace(GaiaClass=Client)
        return original_import(name, *args, **kwargs)

    mocker.patch('builtins.__import__', side_effect=importing)
    selection = 'select source_id from gaiadr3.gaia_source' if query_input else sources
    with log.log_to_list() as records:
        output, _ = calibrate(selection, release=RELEASES.dr3, save_file=False, disable_info=quiet)
    assert len(output) == 1
    printed = capsys.readouterr()
    assert 'Default client announcement' not in printed.out
    assert printed.out.count('Archive announcement') == int(not quiet)
    messages = [record.getMessage() for record in records]
    assert 'Archive warning remains visible' in messages
    assert ('DataLink progress' in messages) is not quiet
    assert ('Query finished.' in messages) == (query_input and not quiet)
    assert ('Retrieving query results' in messages) == (query_input and not quiet)
    if quiet:
        assert printed.out == ''
