import pandas as pd
import pytest

from gaiaxpy import get_required_columns
from gaiaxpy.core.generic_variables import RELEASES, release_solution_id
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader import required_columns as definitions
from gaiaxpy.input_reader.dataframe_reader import DataFrameReader
from gaiaxpy.input_reader.file_reader import FileReader, FileParserSelector
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.continuous import (dr3_mean_spectra_csv_file, dr3_mean_spectra_fits_file,
                                    dr3_mean_spectra_xml_binary_file, dr3_mean_spectra_avro_file)


def test_solution_id_is_optional_for_all_registered_readers():
    assert set(definitions.OPTIONAL_INPUT_COLS) == set(definitions.MANDATORY_INPUT_COLS)
    assert all('solution_id' not in columns for columns in definitions.MANDATORY_INPUT_COLS.values())


@pytest.mark.parametrize('name', ['calibrate', 'convert', 'generate', 'get_inverse_covariance_matrix',
                                  'get_inverse_square_root_covariance_matrix'])
def test_complete_band_groups_in_public_requirements_and_readers(name):
    expected = ['source_id']
    for band in BANDS:
        expected += [f'{band}_{field}' for field in ('n_parameters', 'coefficients', 'standard_deviation',
                                                     'coefficient_errors', 'coefficient_correlations')]
    requirements = get_required_columns(name)
    assert requirements.required == expected
    assert requirements.optional['release identification'] == ['solution_id']
    display = str(requirements)
    positions = [display.index(column + ' (') for column in expected]
    assert positions == sorted(positions)
    reader = DataFrameReader(pd.DataFrame(columns=expected), name, False)
    assert reader.required_columns == expected
    assert reader.requested_columns == expected


@pytest.mark.parametrize('column', ['solution_id', 'solutionId'])
@pytest.mark.parametrize('identifier', [int(release_solution_id[RELEASES.dr3][0]), 123456789])
def test_dataframe_preserves_optional_identifiers_for_release_validation(column, identifier):
    data = pd.read_csv(dr3_mean_spectra_csv_file).iloc[:1].drop(columns=['solution_id'])
    data[column] = identifier
    parsed, _ = DataFrameReader(data, 'convert', False, disable_info=True).read()
    assert parsed[column].iloc[0] == identifier
    reader = InputReader(data, 'convert', truncation=False, release=RELEASES.dr3)
    if identifier == 123456789:
        with pytest.raises(ValueError, match='do not correspond to a known data release'):
            reader.read()
    else:
        assert reader.read()[2] == RELEASES.dr3


def _write_mean_file(tmp_path, extension, include_id):
    path = tmp_path / f'mean.{extension}'
    if extension in ('csv', 'ecsv'):
        data = pd.read_csv(dr3_mean_spectra_csv_file).iloc[:1]
        if not include_id:
            data = data.drop(columns=['solution_id'])
        if extension == 'ecsv':
            from astropy.table import Table
            Table.from_pandas(data).write(path, format='ascii.ecsv')
        else:
            data.to_csv(path, index=False)
    elif extension in ('fits', 'xml'):
        from astropy.table import Table
        source = dr3_mean_spectra_fits_file if extension == 'fits' else dr3_mean_spectra_xml_binary_file
        table = Table.read(source, format='fits' if extension == 'fits' else 'votable')[:1]
        if not include_id:
            table.remove_column('solution_id')
        table.write(path, format='fits' if extension == 'fits' else 'votable')
    else:
        from copy import deepcopy
        from fastavro import reader, writer
        with open(dr3_mean_spectra_avro_file, 'rb') as stream:
            records = reader(stream)
            schema = deepcopy(records.writer_schema)
            record = next(records)
        if not include_id:
            del record['solutionId']
            schema['fields'] = [field for field in schema['fields'] if field['name'] != 'solutionId']
        with open(path, 'wb') as stream:
            writer(stream, schema, [record])
    return path


@pytest.mark.parametrize('extension', ['csv', 'ecsv', 'fits', 'xml', 'avro'])
@pytest.mark.parametrize('include_id', [False, True])
def test_mean_files_accept_absent_solution_id_and_preserve_present_id(tmp_path, extension, include_id):
    path = _write_mean_file(tmp_path, extension, include_id)
    parsed, _ = FileReader(FileParserSelector('convert'), path, False, disable_info=True).read()
    assert ('solution_id' in parsed) == include_id
    if include_id:
        assert str(parsed['solution_id'].iloc[0]) in release_solution_id[RELEASES.dr3]
    else:
        output, _, release = InputReader(path, 'convert', truncation=False, release=RELEASES.dr3).read()
        assert release == RELEASES.dr3
        assert 'solution_id' not in output


@pytest.mark.parametrize('column', ['solution_id', 'solutionId'])
def test_unknown_numeric_solution_id_in_file_is_not_discarded(tmp_path, column):
    data = pd.read_csv(dr3_mean_spectra_csv_file).iloc[:1]
    data = data.drop(columns=['solution_id'])
    data[column] = 123456789
    path = tmp_path / 'unknown.csv'
    data.to_csv(path, index=False)
    with pytest.raises(ValueError, match='do not correspond to a known data release'):
        InputReader(path, 'convert', truncation=False, release=RELEASES.dr3).read()


def test_both_solution_id_names_are_preserved_and_rejected():
    data = pd.read_csv(dr3_mean_spectra_csv_file).iloc[:1]
    data['solutionId'] = data['solution_id']
    with pytest.raises(ValueError, match="only one of 'solution_id' or 'solutionId'"):
        InputReader(data, 'convert', truncation=False, release=RELEASES.dr3).read()
