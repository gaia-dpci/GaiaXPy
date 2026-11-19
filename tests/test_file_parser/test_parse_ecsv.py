import csv
import gzip
from copy import deepcopy
from io import BytesIO, StringIO

import numpy as np
import pandas as pd
import pytest
from astropy.table import MaskedColumn, Table

from gaiaxpy.core.custom_errors import SelectorNotImplementedError
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.file_parser.parse_generic import GenericParser
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.file_parser.parse_inverse import InverseBasesParser
from gaiaxpy.input_reader.required_columns import CORR_INPUT_COLUMNS, MANDATORY_INPUT_COLS
from gaiaxpy.output.photometry_data import PhotometryData
from tests.files.continuous import dr3_mean_spectra_ecsv_file


@pytest.fixture
def example(tmp_path):
    table = Table()
    table['source_id'] = np.array([9007199123456789, 9007199987654321], dtype=np.int64)
    table['label'] = ['001', 'null']
    table['signal'] = np.array([1.234567891234, 2.345678912345], dtype=np.float32)
    table['flux'] = [[1., 2.], [3., 4.]]
    table['matrix'] = np.arange(8, dtype=np.float64).reshape(2, 2, 2)
    table['signal'].unit = 'nm'
    table['signal'].description = 'A description with α, "quotes" and #.'
    table['signal'].format = '.9g'
    table['signal'].meta = {'ucd': 'em.wl'}
    table.meta = {'observer': 'User', 'nested': {'versions': ['1', '2']},
                  'gaiaxpy_metadata': {'input_only': True}}
    path = tmp_path / 'spectra.ecsv'
    table.write(path, format='ascii.ecsv')
    return path, table


@pytest.mark.parametrize('delimiter', [' ', ','])
def test_header_types_shapes_units_and_metadata_are_used(example, delimiter):
    path, table = example
    table.write(path, format='ascii.ecsv', delimiter=delimiter, overwrite=True)
    frame, extension = GenericParser().parse_file(path, disable_info=True)
    assert extension == 'ecsv'
    assert frame['source_id'].tolist() == [9007199123456789, 9007199987654321]
    assert frame['label'].tolist() == ['001', 'null']
    assert frame['signal'].dtype == np.dtype('float64')
    expected_signal = pd.read_csv(path, comment='#', sep=delimiter, **CSV_FLOAT_PRECISION_KWARGS)['signal']
    np.testing.assert_array_equal(frame['signal'], expected_signal)
    np.testing.assert_array_equal(frame['flux'].iloc[0], [1., 2.])
    np.testing.assert_array_equal(frame['matrix'].iloc[1], table['matrix'][1])
    assert frame['matrix'].iloc[1].shape == (2, 2)
    header = frame.attrs['ecsv_metadata']
    assert header['meta'] == table.meta
    assert header['columns']['signal'] == {'unit': 'nm', 'description': table['signal'].description,
                                           'format': '.9g', 'meta': {'ucd': 'em.wl'}, 'datatype': 'float32'}
    assert 'gaiaxpy_metadata' not in frame.attrs


def test_ecsv_dispatch_does_not_call_the_csv_reader(example, monkeypatch):
    path, _ = example
    parser = GenericParser()
    assert parser.get_parser('ecsv') == parser._parse_ecsv
    monkeypatch.setattr(parser, '_parse_csv', lambda *a, **k: pytest.fail('ECSV used the CSV reader'))
    assert len(parser.parse_file(path, disable_info=True)[0]) == 2


@pytest.mark.parametrize('kind', ['text', 'binary', 'gzip'])
def test_streams_remain_open_and_gzip_needs_no_decompressed_file(example, kind):
    path, _ = example
    if kind == 'gzip':
        compressed = path.with_name('spectra.ECSV.GZ')
        with gzip.open(compressed, 'wb') as stream:
            stream.write(path.read_bytes())
        before = set(path.parent.iterdir())
        actual, extension = GenericParser().parse_file(compressed, disable_info=True)
        assert extension == 'ecsv'
        assert set(path.parent.iterdir()) == before
    else:
        stream = StringIO(path.read_text()) if kind == 'text' else BytesIO(path.read_bytes())
        actual = GenericParser()._parse_ecsv(stream)
        assert not stream.closed
    expected, _ = GenericParser().parse_file(path, disable_info=True)
    pd.testing.assert_frame_equal(actual, expected, check_dtype=False)
    assert actual.attrs == expected.attrs


def test_column_selection_and_optional_solution_id_alias(example):
    path, table = example
    table['solutionId'] = np.array([4545464647474848] * 2, dtype=np.int64)
    table.write(path, format='ascii.ecsv', overwrite=True)
    parser = GenericParser()
    parser.optional_columns = ['solution_id', 'absent']
    frame = parser._parse_ecsv(path, _usecols=['source_id', 'signal'])
    assert list(frame) == ['source_id', 'signal', 'solutionId']
    assert set(frame.attrs['ecsv_metadata']['columns']) == set(frame.columns)
    with pytest.raises(KeyError):
        parser._parse_ecsv(path, _usecols=['missing'])


def test_gaia_nulls_do_not_erase_literal_null_strings(tmp_path):
    path = tmp_path / 'nulls.ecsv'
    path.write_text('''# %ECSV 1.0
# ---
# delimiter: ','
# datatype:
# - {name: source_id, datatype: int64}
# - {name: flux, datatype: string, subtype: 'float64[null]'}
# - {name: label, datatype: string}
# - {name: flag, datatype: bool}
source_id,flux,label,flag
9007199123456789,"[1,null]",null,null
null,null,"null",True
''')
    frame, _ = GenericParser().parse_file(path, disable_info=True)
    assert frame['source_id'].iloc[0] == 9007199123456789
    assert pd.isna(frame['source_id'].iloc[1])
    np.testing.assert_allclose(frame['flux'].iloc[0], [1., np.nan], equal_nan=True)
    assert pd.isna(frame['flux'].iloc[1])
    assert frame['label'].tolist() == ['null', 'null']
    assert pd.isna(frame['flag'].iloc[0])
    assert frame['flag'].iloc[1] is True


@pytest.mark.parametrize('parser,column', [(InverseBasesParser, 'inverseBasesCoefficients')])
@pytest.mark.parametrize('declared_arrays', [False, True], ids=['string-array', 'native-array'])
def test_subclasses_keep_their_array_defaults(parser, column, declared_arrays, tmp_path):
    table = Table({'source_id': [1], column: [[1., 2.]] if declared_arrays else ['[1,2]']})
    path = tmp_path / 'arrays.ecsv'
    table.write(path, format='ascii.ecsv')
    frame, _ = parser().parse_file(path, disable_info=True)
    np.testing.assert_array_equal(frame[column].iloc[0], [1., 2.])


def test_matrix_conversion_uses_column_pairs(tmp_path):
    table = Table({'size': [2], 'correlation': [[1., .25, 1.]]})
    path = tmp_path / 'matrix.ecsv'
    table.write(path, format='ascii.ecsv')
    frame = GenericParser()._parse_ecsv(path, _matrix_columns=[('size', 'correlation')])
    np.testing.assert_array_equal(frame['correlation'].iloc[0], [[1., .25], [.25, 1.]])


def test_continuous_reader_preserves_selection_renaming_and_covariances():
    requested = MANDATORY_INPUT_COLS['convert'] + CORR_INPUT_COLUMNS + ['bp_n_measurements']
    parser = InternalContinuousParser(requested, additional_columns={'measurements': ['bp_n_measurements']})
    frame, extension = parser.parse_file(dr3_mean_spectra_ecsv_file, disable_info=True)
    assert extension == 'ecsv'
    assert 'measurements' in frame and 'bp_n_measurements' not in frame
    assert frame['bp_coefficient_correlations'].iloc[0].shape == (55, 55)
    assert frame['rp_covariance_matrix'].iloc[0].shape == (55, 55)
    assert 'ecsv_metadata' in frame.attrs
    with pytest.raises(SelectorNotImplementedError, match='ECSV'):
        InternalContinuousParser(requested, selector=lambda r: True).parse_file(
            dr3_mean_spectra_ecsv_file, disable_info=True)


@pytest.mark.parametrize('content', [
    'source_id,flux\n1,2\n',
    '# %ECSV 1.0\n# ---\n# datatype: [\nsource_id\n1\n',
    '# %ECSV 1.0\n# ---\n# datatype:\n# - {name: a, datatype: int64}\nb\n1\n',
    '# %ECSV 1.0\n# ---\n# datatype:\n# - {name: a, datatype: int64}\na\nnot-an-integer\n',
    '# %ECSV 1.0\n# ---\n# datatype:\n# - {name: flux, datatype: string, subtype: "float64[2]"}\nflux\n[1]\n'
])
def test_invalid_ecsv_is_not_silently_read_as_csv(content, tmp_path):
    path = tmp_path / 'invalid.ecsv'
    path.write_text(content)
    with pytest.raises(ValueError):
        GenericParser().parse_file(path, disable_info=True)


def test_empty_table_keeps_columns_and_metadata(example):
    path, table = example
    table[:0].write(path, format='ascii.ecsv', overwrite=True)
    frame, _ = GenericParser().parse_file(path, disable_info=True)
    assert len(frame) == 0
    assert list(frame) == table.colnames
    assert frame.attrs['ecsv_metadata']['meta'] == table.meta


def test_metadata_copies_are_independent(example):
    path, table = example
    first = GenericParser()._parse_ecsv(path)
    second = GenericParser()._parse_ecsv(path)
    before = deepcopy(second.attrs)
    first.attrs['ecsv_metadata']['meta']['nested']['versions'].append('changed')
    first.attrs['ecsv_metadata']['columns']['signal']['meta']['ucd'] = 'changed'
    assert second.attrs == before
    assert table.meta['nested']['versions'] == ['1', '2']


def test_gaiaxpy_photometry_outputs_can_be_read_as_ecsv(tmp_path):
    data = pd.DataFrame({'source_id': [9007199123456789], 'DR3_Sdss_mag_g': [12.345678901]})
    data.attrs['gaiaxpy_metadata'] = {'example': 'metadata'}
    PhotometryData(data).save(True, tmp_path, 'photometry', 'ecsv', 'csv', disable_info=True)
    frame, _ = GenericParser().parse_file(tmp_path / 'photometry.ecsv', disable_info=True)
    assert frame['source_id'].iloc[0] == 9007199123456789
    np.testing.assert_allclose(frame['DR3_Sdss_mag_g'], data['DR3_Sdss_mag_g'], rtol=1e-6)
    assert 'gaiaxpy_metadata' not in frame.attrs
    assert 'gaiaxpy_metadata' in frame.attrs['ecsv_metadata']['meta']


@pytest.mark.parametrize('compressed', [False, True])
def test_large_array_cells_and_csv_limit_restoration(tmp_path, compressed):
    table = Table({'source_id': [1], 'flux': np.arange(100000, dtype=float).reshape(1, -1)})
    path = tmp_path / 'large.ecsv'
    table.write(path, format='ascii.ecsv')
    if compressed:
        packed = path.with_suffix('.ecsv.gz')
        with gzip.open(packed, 'wb') as stream:
            stream.write(path.read_bytes())
        path = packed
    previous_limit = csv.field_size_limit()
    frame, _ = GenericParser().parse_file(path, disable_info=True)
    np.testing.assert_array_equal(frame['flux'].iloc[0], table['flux'][0])
    assert csv.field_size_limit() == previous_limit


def test_csv_limit_restored_when_ecsv_reading_fails():
    previous_limit = csv.field_size_limit()
    with pytest.raises(ValueError):
        GenericParser()._parse_ecsv(BytesIO(b'not ECSV'))
    assert csv.field_size_limit() == previous_limit


@pytest.mark.parametrize('dtype,value', [('int64', 9007199123456789), ('uint64', 2 ** 64 - 1),
                                         ('int32', 2 ** 31 - 1)])
@pytest.mark.parametrize('mask', [[False, True], [True, True]])
def test_masked_integer_columns_preserve_exact_values(tmp_path, dtype, value, mask):
    table = Table()
    table['identifier'] = MaskedColumn([value, 0], dtype=dtype, mask=mask)
    table['label'] = ['first', 'second']
    path = tmp_path / 'integers.ecsv'
    table.write(path, format='ascii.ecsv')
    frame, _ = GenericParser().parse_file(path, disable_info=True)
    assert frame['identifier'].dtype.name == {'int64': 'Int64', 'uint64': 'UInt64', 'int32': 'Int32'}[dtype]
    for index, missing in enumerate(mask):
        if missing:
            assert pd.isna(frame['identifier'].iloc[index])
        else:
            assert int(frame['identifier'].iloc[index]) == value
    assert frame['label'].tolist() == ['first', 'second']
