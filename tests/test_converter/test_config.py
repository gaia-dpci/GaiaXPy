import pandas as pd
import pytest

from gaiaxpy.config.paths import hermite_bases_file
from gaiaxpy.converter.config import get_unique_id, parse_config


@pytest.fixture(scope='module')
def columns():
    columns = ['dimension', 'range', 'normalizedRange', 'uniqueId', 'transformedSetDimension', 'transformationMatrix']
    yield columns


@pytest.fixture(scope='module')
def parsed_config():
    bases_config = parse_config(hermite_bases_file)  # id 7 not in the config file
    bands_config = bases_config.hermiteFunction

    bp_config = bands_config.bpConfig
    rp_config = bands_config.rpConfig
    bp_config_dict = {field: getattr(bp_config, field) for field in bp_config._fields}
    rp_config_dict = {field: getattr(rp_config, field) for field in rp_config._fields}

    yield pd.DataFrame([bp_config_dict, rp_config_dict])


def test_parse_configuration_file_type(parsed_config):
    assert isinstance(parsed_config, pd.DataFrame)


def test_parse_configuration_dimensions(parsed_config):
    assert parsed_config.shape == (2, 6)


def test_parse_configuration_columns(parsed_config, columns):
    assert list(parsed_config.columns) == columns


def test_load_config_type(parsed_config):
    assert isinstance(parsed_config, pd.DataFrame)


def test_load_config_dimensions(parsed_config):
    assert parsed_config.shape == parsed_config.shape


def test_get_config_not_empty_df(columns, parsed_config):
    not_empty_df = get_unique_id(parsed_config, 57)  # id 57 in the config file
    assert not_empty_df.shape == (1, 6)
    assert isinstance(not_empty_df, pd.DataFrame)
    assert list(not_empty_df) == columns


def test_get_config_empty_df(columns, parsed_config):
    empty_df = get_unique_id(parsed_config, 7)
    assert empty_df.shape == (0, 6)
    assert isinstance(empty_df, pd.DataFrame)
    assert list(empty_df) == columns
