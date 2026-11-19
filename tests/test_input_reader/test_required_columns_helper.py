import pandas as pd
import pytest

import gaiaxpy
from gaiaxpy import get_required_columns
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader import required_columns as definitions
from gaiaxpy.input_reader.dataframe_reader import DataFrameReader
from gaiaxpy.input_reader.required_columns import ColumnRequirements


def test_every_public_export_has_an_explicit_column_classification():
    classified = (set(definitions._READER_FUNCTIONS) | definitions._CUSTOM_COLUMN_FUNCTIONS
                  | set(definitions._NON_TABULAR_FUNCTIONS) | definitions._NON_FUNCTION_EXPORTS)
    missing = set(gaiaxpy.__all__) - classified
    stale = classified - set(gaiaxpy.__all__)
    assert not missing, f'New public exports need a column description or explicit exclusion: {sorted(missing)}'
    assert not stale, f'Remove classifications for exports no longer public: {sorted(stale)}'


@pytest.mark.parametrize('name', sorted(set(definitions._READER_FUNCTIONS) | definitions._CUSTOM_COLUMN_FUNCTIONS))
def test_all_tabular_functions_are_described_by_name_and_callable(name):
    result = get_required_columns(name)
    assert isinstance(result, ColumnRequirements)
    assert result == get_required_columns(getattr(gaiaxpy, name))
    assert result.function == name
    assert set(vars(result)) == {'function', 'required', 'alternatives', 'conditional', 'optional', 'notes',
                                 'column_info'}


@pytest.mark.parametrize('name', sorted(definitions._NON_TABULAR_FUNCTIONS))
def test_non_tabular_functions_have_an_explanatory_error(name):
    with pytest.raises(ValueError, match='does not consume tabular spectra or photometry'):
        get_required_columns(name)


@pytest.mark.parametrize('name', ['missing', '_calibrate', 'PhotometricSystem', 'Calibrate'])
def test_unknown_or_non_function_names_list_supported_functions(name):
    with pytest.raises(ValueError, match='Supported functions: .*apply_error_correction.'):
        get_required_columns(name)


@pytest.mark.parametrize('value', [None, 12, [], lambda: None])
def test_invalid_arguments(value):
    with pytest.raises(TypeError, match='public GaiaXPy function'):
        get_required_columns(value)


@pytest.mark.parametrize('name', ['calibrate', 'convert', 'generate'])
def test_reported_requirements_agree_with_dataframe_reader(name):
    result = get_required_columns(name)
    columns = result.required + result.optional['release identification']
    data = pd.DataFrame(columns=columns)
    expected = DataFrameReader.get_required_columns(data, definitions.MANDATORY_INPUT_COLS[name],
                                                    definitions.requires_coefficient_errors(name))
    assert set(result.required) == set(expected)
    truncated_reader = DataFrameReader(data, name, truncation=True)
    assert set(truncated_reader.required_columns) == set(result.required +
                                                         result.conditional['truncation=True'])
    assert 'solution_id' in truncated_reader.requested_columns


def test_result_copies_do_not_change_readers_or_later_results():
    original = get_required_columns('calibrate')
    modified = get_required_columns('calibrate')
    modified.required.clear()
    modified.alternatives['unexpected'] = ['column']
    modified.conditional['truncation=True'].append('unwanted')
    modified.optional['release identification'].clear()
    modified.notes.clear()
    assert get_required_columns('calibrate') == original
    assert not original.alternatives
    assert definitions.TRUNCATION_COLS == original.conditional['truncation=True']


@pytest.mark.parametrize('name', ['get_inverse_covariance_matrix', 'get_inverse_square_root_covariance_matrix'])
def test_inverse_matrix_requirements_include_consumed_uncertainty_fields(name):
    result = get_required_columns(name)
    assert set(definitions.CORR_INPUT_COLUMNS) <= set(result.required)
    assert not result.alternatives
    assert not set(definitions.COV_INPUT_COLUMNS) & set(result.required)
    columns = result.required + result.optional['release identification']
    assert set(DataFrameReader.get_required_columns(pd.DataFrame(columns=columns),
                                                    definitions.MANDATORY_INPUT_COLS[name],
                                                    definitions.requires_coefficient_errors(name))) == set(
        result.required)


def test_variable_requirements_are_visible_without_options():
    plotting = get_required_columns('plot_spectra')
    assert plotting.required == ['source_id', 'flux', 'flux_error']
    assert ['xp'] in plotting.conditional.values()
    assert any('data_type' in note for note in plotting.notes)
    photometry = get_required_columns('apply_error_correction')
    assert photometry.required == ['{system}_flux_error_{band}', 'DR3_GaiaVega_mag_G']
    assert photometry.optional['source identification'] == ['source_id']
    assert not photometry.conditional


@pytest.mark.parametrize('name', sorted(set(definitions._READER_FUNCTIONS) | definitions._CUSTOM_COLUMN_FUNCTIONS))
def test_lookup_needs_no_input_files_or_archive(mocker, name):
    mocker.patch('builtins.open', side_effect=AssertionError('Unexpected file access'))
    mocker.patch('gaiaxpy.input_reader.input_reader.InputReader.read',
                 side_effect=AssertionError('Unexpected input or Archive access'))
    assert get_required_columns(name).function == name


def test_display_puts_minimum_requirements_before_additional_information(capsys):
    result = ColumnRequirements('example', ['source_id'], {'errors': ['errors']},
                                {'truncation=True': ['n_relevant']}, {'identification': ['solution_id']},
                                ['Pass sampling separately.'])
    expected = ('example\n\nRequired input columns:\n  source_id\n\n'
                'Also required (provide one complete group):\n  errors:\n    errors\n\n'
                'Conditional requirements:\n  truncation=True:\n    n_relevant\n\n'
                'Optional columns:\n  identification:\n    solution_id\n\n'
                'Notes:\n  - Pass sampling separately.')
    assert str(result) == repr(result) == expected
    print(result)
    assert capsys.readouterr().out == expected + '\n'


def test_default_collections_are_independent():
    first = ColumnRequirements('first')
    second = ColumnRequirements('second')
    first.required.append('extra')
    first.alternatives['extra'] = ['column']
    assert not second.required
    assert not second.alternatives


@pytest.mark.parametrize('name', ['calibrate', 'convert', 'generate'])
def test_archive_display_and_attributes_include_the_same_complete_requirements(name):
    result = get_required_columns(name)
    original = get_required_columns(name)
    display = repr(result)
    minimum = display.split('Conditional requirements:')[0]
    for column in definitions.CORR_INPUT_COLUMNS:
        assert f'  {column} (array of floats)' in minimum
    assert 'Also required' not in display
    for column in definitions.COV_INPUT_COLUMNS:
        assert column not in display
    assert 'covariances' not in display
    assert not result.alternatives
    assert set(definitions.CORR_INPUT_COLUMNS) <= set(result.required)
    assert result._display_fields()[0] == result.required
    assert not set(definitions.COV_INPUT_COLUMNS) & set(result.column_info)
    assert result == original


@pytest.mark.parametrize('name', sorted(set(definitions._READER_FUNCTIONS) | definitions._CUSTOM_COLUMN_FUNCTIONS))
def test_every_reported_column_has_simple_type_and_description(name):
    result = get_required_columns(name)
    columns = set(result.required)
    for groups in (result.alternatives, result.conditional, result.optional):
        for group in groups.values():
            columns.update(group)
    assert set(result.column_info) == columns
    for info in result.column_info.values():
        assert info['type'] in {'integer', 'float', 'string', 'array of floats', 'array of integers'}
        assert info['description']


@pytest.mark.parametrize('band', list(BANDS))
def test_continuous_array_lengths_and_parameter_types(band):
    info = get_required_columns('calibrate').column_info
    count = f'{band}_n_parameters'
    assert info[count]['type'] == 'integer'
    assert info[f'{band}_coefficients']['length'] == count
    assert info[f'{band}_coefficient_errors']['length'] == count
    assert info[f'{band}_coefficient_correlations']['length'] == f'{count} * ({count} - 1) / 2'


def test_column_metadata_is_independent_between_results():
    first = get_required_columns('calibrate')
    first.column_info['bp_coefficients']['type'] = 'changed'
    first.column_info.clear()
    assert get_required_columns('calibrate').column_info['bp_coefficients']['type'] == 'array of floats'


@pytest.mark.parametrize('name', sorted(set(definitions._READER_FUNCTIONS) | definitions._CUSTOM_COLUMN_FUNCTIONS))
def test_public_attributes_match_display_and_hide_internal_covariance_columns(name):
    result = get_required_columns(name)
    assert result._display_fields()[0] == result.required
    assert not result.alternatives
    for column in definitions.COV_INPUT_COLUMNS:
        assert column not in result.required
        assert column not in result.column_info
        assert column not in str(result)


@pytest.mark.parametrize('name', ['calibrate', 'convert', 'generate'])
def test_internal_dataframe_reader_still_selects_covariance_representation(name):
    columns = definitions.MANDATORY_INPUT_COLS[name] + definitions.COV_INPUT_COLUMNS
    actual = DataFrameReader.get_required_columns(pd.DataFrame(columns=columns),
                                                  definitions.MANDATORY_INPUT_COLS[name],
                                                  definitions.requires_coefficient_errors(name))
    assert actual == definitions.order_input_columns(columns)


@pytest.mark.parametrize('band', list(BANDS))
def test_missing_band_guidance_matches_release_detection(band):
    import numpy as np
    from gaiaxpy.core.release_resolution import _compatible_releases_from_n_parameters
    from gaiaxpy.core.generic_variables import RELEASES, n_params_dict

    present = BANDS.rp if band == BANDS.bp else BANDS.bp
    data = pd.DataFrame({f'{band}_n_parameters': [np.nan],
                         f'{present}_n_parameters': [n_params_dict[RELEASES.dr3][present]]})
    assert RELEASES.dr3 in _compatible_releases_from_n_parameters(data)
    data[f'{band}_n_parameters'] = 0
    with pytest.raises(ValueError, match='do not correspond to a known'):
        _compatible_releases_from_n_parameters(data)
    assert 'Do not use n_parameters=0' in str(get_required_columns('calibrate'))
