"""Compare CSV and ECSV values before and after GaiaXPy calculations."""
import csv
import gzip
from io import StringIO

import numpy as np
import pandas as pd
import pytest

from gaiaxpy.file_parser.parse_generic import GenericParser
from tests.utils.utils import assert_dfs_equal


def _assert_identical_numbers(actual, expected):
    """Compare scalar and array values exactly, accepting pandas missing values."""
    actual = actual.astype(object).where(actual.notna(), np.nan)
    expected = expected.astype(object).where(expected.notna(), np.nan)
    assert_dfs_equal(actual, expected, rtol=0, atol=0)


def _write_input(path, text, compressed):
    """Write plain or gzip input without changing its numerical text."""
    if compressed:
        path = path.with_suffix(path.suffix + '.gz')
        with gzip.open(path, 'wt', encoding='utf-8') as stream:
            stream.write(text)
    else:
        path.write_text(text, encoding='utf-8')
    return path


@pytest.mark.parametrize('compressed', [False, True], ids=['plain', 'gzip'])
@pytest.mark.parametrize('float_type', ['float32', 'float64'])
@pytest.mark.parametrize('array_type', ['string', 'fixed', 'variable'])
def test_identical_numeric_text_matches_csv(tmp_path, compressed, float_type, array_type):
    # These decimal strings distinguish float64 parsing from a float32 cast,
    # including values outside float32's range. Neither file is made by
    # first casting the values to float32.
    numbers = ['1.234567891234567', '-9.876543219876543e-25', '1.0000000000000002',
               '-0.0', '1.234567891234567e100', '2.2250738585072014e-308', '5e-324',
               'nan', 'inf', '-inf', '']
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['source_id', 'signal', 'flux', 'size', 'correlation'])
    identifiers = [2 ** 53 + 1 + 2 * index for index in range(len(numbers))]
    for identifier, number in zip(identifiers, numbers, strict=True):
        array_number = '0.0' if number in ('nan', 'inf', '-inf') else number
        flux = f'[{array_number},1.234567891234567]' if number else ''
        writer.writerow([identifier, number, flux, 2, '[1,0.1234567891234567,1]'])
    body = buffer.getvalue()
    flux_subtype = {'string': '', 'fixed': f", subtype: '{float_type}[2]'",
                    'variable': f", subtype: '{float_type}[null]'"}[array_type]
    header = f'''# %ECSV 1.0
# ---
# delimiter: ','
# datatype:
# - {{name: source_id, datatype: int64}}
# - {{name: signal, datatype: {float_type}}}
# - {{name: flux, datatype: string{flux_subtype}}}
# - {{name: size, datatype: int16}}
# - {{name: correlation, datatype: string, subtype: '{float_type}[3]'}}
'''
    csv_path = _write_input(tmp_path / 'numbers.csv', body, compressed)
    ecsv_path = _write_input(tmp_path / 'numbers.ecsv', header + body, compressed)
    before = ecsv_path.read_bytes()
    parser = GenericParser()
    options = {'_array_columns': ['flux'], '_matrix_columns': [('size', 'correlation')]}
    with parser.get_input_context(csv_path) as source:
        expected = parser._parse_csv(source, **options)
    with parser.get_input_context(ecsv_path) as source:
        actual = parser._parse_ecsv(source, **options)
    assert actual['source_id'].tolist() == expected['source_id'].tolist() == identifiers
    assert actual['signal'].dtype == np.dtype('float64')
    _assert_identical_numbers(actual, expected)
    assert np.signbit(actual['signal'].iloc[3])
    assert actual['flux'].iloc[0].dtype == np.dtype('float64')
    declarations = actual.attrs['ecsv_metadata']['columns']
    assert declarations['signal']['datatype'] == float_type
    if array_type != 'string':
        assert declarations['flux']['subtype'] == f'{float_type}[{2 if array_type == "fixed" else "null"}]'
    assert declarations['correlation']['subtype'] == f'{float_type}[3]'
    assert ecsv_path.read_bytes() == before
    assert set(tmp_path.iterdir()) == {csv_path, ecsv_path}


@pytest.mark.parametrize('identifier', [2 ** 53 + 1, 2 ** 63 - 1])
def test_large_identifiers_with_missing_values_remain_exact(tmp_path, identifier):
    # Float64 cannot represent these integers exactly. Missing rows must not
    # force the integer column through a floating-point representation.
    path = tmp_path / 'identifiers.ecsv'
    path.write_text(f'''# %ECSV 1.0
# ---
# datatype:
# - {{name: source_id, datatype: int64}}
source_id
{identifier}
""
''')
    frame, _ = GenericParser().parse_file(path, disable_info=True)
    assert frame['source_id'].dtype == pd.Int64Dtype()
    assert int(frame['source_id'].iloc[0]) == identifier
    assert pd.isna(frame['source_id'].iloc[1])
