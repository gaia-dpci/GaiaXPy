from types import SimpleNamespace

import pandas as pd
import pytest

from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.input_reader import required_columns as definitions
from gaiaxpy.input_reader.archive_reader import ArchiveReader
from gaiaxpy.input_reader.dataframe_reader import DataFrameReader
from gaiaxpy.input_reader.file_reader import FileReader


def test_every_reader_schema_declares_its_uncertainty_requirement():
    assert set(definitions.MANDATORY_INPUT_COLS) <= set(definitions.COEFFICIENT_ERRORS_REQUIRED)
    assert all(isinstance(value, bool) for value in definitions.COEFFICIENT_ERRORS_REQUIRED.values())


@pytest.mark.parametrize('reader_type', ['dataframe', 'file', 'archive'])
@pytest.mark.parametrize('required', [False, True])
@pytest.mark.parametrize('columns', [['source_id'], ['source_id', 'bp_coefficients']])
def test_readers_follow_explicit_flag_independently_of_column_names(monkeypatch, reader_type, required, columns):
    name = 'test_product'
    monkeypatch.setitem(definitions.MANDATORY_INPUT_COLS, name, columns)
    monkeypatch.setitem(definitions.COEFFICIENT_ERRORS_REQUIRED, name, required)
    if reader_type == 'dataframe':
        data = pd.DataFrame(columns=columns + definitions.CORR_INPUT_COLUMNS)
        reader = DataFrameReader(data, name, truncation=False)
    elif reader_type == 'file':
        reader = FileReader(SimpleNamespace(function_name=name), 'input.csv', truncation=False)
    else:
        reader = ArchiveReader(name, False, None, None, release=RELEASES.dr3)
    expected = columns + (definitions.CORR_INPUT_COLUMNS if required else [])
    assert reader.required_columns == definitions.order_input_columns(expected)


def test_dataframe_without_errors_is_accepted_when_flag_is_false():
    columns = ['source_id', 'bp_coefficients']
    assert DataFrameReader.get_required_columns(pd.DataFrame(columns=columns), columns, False) == columns


def test_dataframe_requires_errors_even_without_coefficient_columns():
    with pytest.raises(ValueError, match='Missing correlation columns'):
        DataFrameReader.get_required_columns(pd.DataFrame(columns=['source_id']), ['source_id'], True)


@pytest.mark.parametrize('name', ['_apply_colour_equation', '_apply_error_correction',
                                  'apply_colour_equation', 'apply_error_correction'])
def test_non_coefficient_products_do_not_require_coefficient_errors(name):
    assert not definitions.requires_coefficient_errors(name)


@pytest.mark.parametrize('name', ['calibrate', '_calibrate', 'convert', '_convert', 'generate', '_generate',
                                  'get_inverse_covariance_matrix', 'get_inverse_square_root_covariance_matrix'])
def test_mean_coefficient_consumers_require_errors(name):
    assert definitions.requires_coefficient_errors(name)


@pytest.mark.parametrize('name', ['unknown_operation', 'convertt', ''])
def test_unregistered_operations_raise_clear_errors(name):
    with pytest.raises(ValueError, match=f'No coefficient error requirement is registered for {name!r}'):
        definitions.requires_coefficient_errors(name)


@pytest.mark.parametrize('reader_type', ['dataframe', 'file', 'archive'])
def test_readers_reject_unregistered_operations(reader_type):
    name = 'unregistered_operation'
    with pytest.raises(ValueError, match='No coefficient error requirement is registered'):
        if reader_type == 'dataframe':
            DataFrameReader(pd.DataFrame({'source_id': [1]}), name, truncation=False)
        elif reader_type == 'file':
            FileReader(SimpleNamespace(function_name=name), 'input.csv', truncation=False)
        else:
            ArchiveReader(name, False, None, None, release=RELEASES.dr3)
