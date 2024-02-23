import pandas as pd
import pytest
from numpy import ndarray, dtype

from gaiaxpy.file_parser.parse_external import ExternalParser
from gaiaxpy.file_parser.parse_generic import InvalidExtensionError
from tests.files.paths import mini_csv_file, no_ext_file


@pytest.fixture
def parser():
    yield ExternalParser()


@pytest.fixture
def parsed_csv_file(parser):
    yield parser._parse_csv(mini_csv_file)


def test_parse_no_extension(parser):
    pytest.raises(InvalidExtensionError, parser.parse_file, no_ext_file)


def test_parse_returns_dataframe(parsed_csv_file):
    assert isinstance(parsed_csv_file, pd.DataFrame)


# 'O' stands for object
def test_column_types(parsed_csv_file):
    assert list(parsed_csv_file.dtypes) == [dtype('int64'), dtype('O'), dtype('O'), dtype('O')]


def test_flux_types(parsed_csv_file):
    assert isinstance(parsed_csv_file['flux'][0], ndarray)
    assert isinstance(parsed_csv_file['flux_error'][0], ndarray)
