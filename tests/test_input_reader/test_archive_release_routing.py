from unittest.mock import Mock

import pandas as pd
import pytest

from gaiaxpy import convert
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.server import (gaia_server, get_release_for_archive, get_retrieval_type_for_archive,
                                 get_server_for_archive)
from gaiaxpy.input_reader.archive_reader import ArchiveReader


def _reader(release, user=None, password=None, retrieval_type=None, credentials_file=None):
    return ArchiveReader(convert, False, user, password, release=release,
                         retrieval_type=retrieval_type, credentials_file=credentials_file)


def _authenticated_gaia():
    gaia = Mock()
    gaia._TapPlus__isLoggedIn = True
    gaia._GaiaClass__gaiadata._TapPlus__isLoggedIn = True
    return gaia


def test_dr3_archive_configuration():
    assert get_server_for_archive(RELEASES.dr3) == gaia_server
    assert get_release_for_archive(RELEASES.dr3) == 'Gaia DR3'
    assert get_retrieval_type_for_archive(RELEASES.dr3) == 'XP_CONTINUOUS'
    assert _reader(RELEASES.dr3).retrieval_type == 'XP_CONTINUOUS'


def test_explicit_retrieval_type_is_preserved():
    reader = _reader(RELEASES.dr3, user='user', retrieval_type='MEAN_SPECTRUM_XP')
    assert reader.retrieval_type == 'MEAN_SPECTRUM_XP'


def test_empty_result_has_no_key():
    assert _reader(RELEASES.dr3, user='user')._get_result_key({}) is None


def test_dr3_does_not_require_login():
    gaia = Mock()
    _reader(RELEASES.dr3)._login(gaia)
    gaia.login.assert_not_called()


@pytest.mark.parametrize('user,password', [('user', None), (None, 'password'), ('user', 'password')])
def test_credentials_file_is_mutually_exclusive_with_user_credentials(user, password):
    gaia = Mock()
    with pytest.raises(ValueError, match='credentials_file cannot be used together'):
        _reader(RELEASES.dr3, user=user, password=password, credentials_file='credentials.txt')._login(gaia)
    gaia.login.assert_not_called()


class _FakeTable:
    def __init__(self, data):
        self._data = data

    def to_pandas(self):
        return pd.DataFrame(self._data)
