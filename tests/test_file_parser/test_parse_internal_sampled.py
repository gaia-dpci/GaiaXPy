import pandas as pd
import pytest
from numpy import ndarray, dtype

from gaiaxpy.file_parser.parse_internal_sampled import InternalSampledParser
from tests.files.paths import con_ref_sampled_csv_path


@pytest.fixture
def parser():
    yield InternalSampledParser()


@pytest.fixture
def parsed_csv_file(parser):
    parsed_csv_file, _ = parser.parse_file(con_ref_sampled_csv_path)
    yield parsed_csv_file


def test_parse_returns_dataframe(parsed_csv_file):
    assert isinstance(parsed_csv_file, pd.DataFrame)


# 'O' stands for object
def test_column_types(parsed_csv_file):
    assert list(parsed_csv_file.dtypes) == [pd.Int64Dtype(), dtype('O'), dtype('O'), dtype('O')]


@pytest.mark.parametrize('column', ['flux', 'error'])
def test_flux_and_error(parsed_csv_file, column):
    assert isinstance(parsed_csv_file[column][0], ndarray)
