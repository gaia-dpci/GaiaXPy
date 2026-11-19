import numpy as np
import pandas as pd
import pytest

from gaiaxpy import convert
from gaiaxpy.core.generic_variables import RELEASES, release_solution_id
from gaiaxpy.core.release_resolution import get_release_from_data
from gaiaxpy.input_reader.input_reader import InputReader


def _release_test_function():
    pass


def _release_data(solution_id=None, bp_n_parameters=None, rp_n_parameters=None):
    data = {'source_id': [1]}
    if solution_id is not None:
        data['solution_id'] = [solution_id]
    if bp_n_parameters is not None:
        data['bp_n_parameters'] = [bp_n_parameters]
    if rp_n_parameters is not None:
        data['rp_n_parameters'] = [rp_n_parameters]
    return pd.DataFrame(data)


def test_release_detected_from_solution_id_before_n_parameters():
    data = _release_data(
        solution_id=release_solution_id[RELEASES.dr3][0],
        bp_n_parameters=51,
        rp_n_parameters=55
    )

    assert get_release_from_data(data, convert) == RELEASES.dr3


@pytest.mark.parametrize('release', [RELEASES.dr3])
def test_release_detected_from_known_solution_id(release):
    data = _release_data(solution_id=release_solution_id[release][0])

    assert get_release_from_data(data, convert) == release


def test_solution_id_alias_is_supported():
    data = pd.DataFrame({
        'source_id': [1],
        'solutionId': [release_solution_id[RELEASES.dr3][0]],
    })

    assert get_release_from_data(data, convert) == RELEASES.dr3


def test_both_solution_id_column_names_raise():
    data = pd.DataFrame({
        'source_id': [1],
        'solution_id': [release_solution_id[RELEASES.dr3][0]],
        'solutionId': [release_solution_id[RELEASES.dr3][0]]
    })

    with pytest.raises(ValueError, match="only one of 'solution_id' or 'solutionId'"):
        get_release_from_data(data, convert)


def test_unknown_solution_id_raises_even_when_n_parameters_identify_release():
    data = _release_data(solution_id='unknown', bp_n_parameters=55, rp_n_parameters=55)

    with pytest.raises(ValueError, match='do not correspond to a known data release'):
        get_release_from_data(data, convert)


def test_explicit_release_does_not_override_unknown_solution_id():
    data = _release_data(solution_id='unknown', bp_n_parameters=55, rp_n_parameters=55)
    reader = InputReader(data, convert, truncation=False, release=RELEASES.dr3)

    with pytest.raises(ValueError, match='do not correspond to a known data release'):
        reader.check_releases_match(data)


@pytest.mark.parametrize(('bp_n_parameters', 'rp_n_parameters', 'expected'), [(55, 55, RELEASES.dr3)])
def test_release_detected_from_n_parameters(bp_n_parameters, rp_n_parameters, expected):
    data = _release_data(bp_n_parameters=bp_n_parameters, rp_n_parameters=rp_n_parameters)

    assert get_release_from_data(data, convert) == expected


@pytest.mark.parametrize('release', [RELEASES.dr3])
def test_explicit_release_resolves_missing_bp_ambiguity(mocker, release):
    parsed = pd.DataFrame({
        'source_id': [1, 2],
        'bp_n_parameters': [np.nan, np.nan],
        'rp_n_parameters': [55, 55]
    })
    mocker.patch('gaiaxpy.input_reader.dataframe_reader.requires_coefficient_errors', return_value=False)
    mocker.patch('gaiaxpy.input_reader.input_reader.DataFrameReader.read', return_value=(parsed, 'csv'))

    _, _, detected_release = InputReader(parsed, _release_test_function, truncation=False, release=release).read()

    assert detected_release == release


@pytest.mark.parametrize('release', [None, RELEASES.dr3])
def test_invalid_n_parameters_raise_regardless_of_explicit_release(mocker, release):
    parsed = pd.DataFrame({
        'source_id': [1],
        'bp_n_parameters': [52],
        'rp_n_parameters': [55]
    })
    mocker.patch('gaiaxpy.input_reader.dataframe_reader.requires_coefficient_errors', return_value=False)
    mocker.patch('gaiaxpy.input_reader.input_reader.DataFrameReader.read', return_value=(parsed, 'csv'))

    with pytest.raises(ValueError, match='bp_n_parameters values.*do not correspond to a known data release'):
        InputReader(parsed, _release_test_function, truncation=False, release=release).read()


def test_conflicting_n_parameters_raise():
    data = pd.DataFrame({'source_id': [1, 2], 'bp_n_parameters': [51, 55], 'rp_n_parameters': [55, 55]})

    with pytest.raises(ValueError, match='bp_n_parameters column contains conflicting values'):
        get_release_from_data(data, convert)


def test_no_bp_or_rp_data_raises():
    data = pd.DataFrame({'source_id': [1, 2], 'bp_n_parameters': [np.nan, np.nan],
                         'rp_n_parameters': [np.nan, np.nan]})

    with pytest.raises(ValueError, match='no BP or RP parameters to process'):
        get_release_from_data(data, convert)


def test_release_detection_returns_none_when_release_columns_are_absent():
    assert get_release_from_data(pd.DataFrame({'source_id': [1]}), convert) is None


@pytest.mark.parametrize('release', [None, RELEASES.dr3])
def test_archive_input_defaults_to_dr3(release):
    assert InputReader._require_archive_release(release) == RELEASES.dr3


def test_explicit_release_is_used_when_dataframe_does_not_identify_release(mocker):
    parsed = pd.DataFrame({'source_id': [1]})
    mocker.patch('gaiaxpy.input_reader.dataframe_reader.requires_coefficient_errors', return_value=False)
    mocker.patch('gaiaxpy.input_reader.input_reader.DataFrameReader.read', return_value=(parsed, 'csv'))

    _, _, release = InputReader(parsed, _release_test_function, truncation=False, release=RELEASES.dr3).read()

    assert release == RELEASES.dr3


def test_missing_release_defaults_to_dr3_when_dataframe_does_not_identify_release(mocker):
    parsed = pd.DataFrame({'source_id': [1]})
    mocker.patch('gaiaxpy.input_reader.dataframe_reader.requires_coefficient_errors', return_value=False)
    mocker.patch('gaiaxpy.input_reader.input_reader.DataFrameReader.read', return_value=(parsed, 'csv'))

    _, _, release = InputReader(parsed, _release_test_function, truncation=False).read()

    assert release == RELEASES.dr3


def test_matching_explicit_and_detected_release_is_accepted(mocker):
    parsed = _release_data(solution_id=release_solution_id[RELEASES.dr3][0])
    mocker.patch('gaiaxpy.input_reader.dataframe_reader.requires_coefficient_errors', return_value=False)
    mocker.patch('gaiaxpy.input_reader.input_reader.DataFrameReader.read', return_value=(parsed, 'csv'))

    _, _, release = InputReader(parsed, _release_test_function, truncation=False, release=RELEASES.dr3).read()

    assert release == RELEASES.dr3
