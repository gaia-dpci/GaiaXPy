import gzip
from shutil import copyfileobj

import pandas.testing as pdt
import pytest

from gaiaxpy import convert
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.file_parser.parse_generic import GenericParser, InvalidExtensionError
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.continuous import (dr3_with_missing_bp_csv_file, dr3_with_missing_bp_ecsv_file,
                                    dr3_with_missing_bp_fits_file, dr3_with_missing_bp_xml_plain_file,
                                    dr3_with_missing_bp_xml_binary_file)

INPUT_FILES = [dr3_with_missing_bp_csv_file, dr3_with_missing_bp_ecsv_file,
               dr3_with_missing_bp_fits_file, dr3_with_missing_bp_xml_plain_file,
               dr3_with_missing_bp_xml_binary_file]


def compress(source, destination):
    with source.open('rb') as input_stream, gzip.open(destination, 'wb') as output_stream:
        copyfileobj(input_stream, output_stream)
    return destination


@pytest.mark.parametrize('source', INPUT_FILES, ids=['csv', 'ecsv', 'fits', 'xml-plain', 'xml-binary'])
@pytest.mark.parametrize('uppercase', [False, True], ids=['lowercase', 'uppercase'])
@pytest.mark.parametrize('as_string', [False, True], ids=['path', 'str'])
def test_gzip_matches_uncompressed(source, uppercase, as_string, tmp_path):
    filename = source.name + '.gz'
    compressed = compress(source, tmp_path / (filename.upper() if uppercase else filename))
    additional_columns = {'measurements': ['bp_n_measurements']}

    def read(path):
        return InputReader(path, convert, truncation=True, additional_columns=additional_columns,
                           disable_info=True).read()

    expected, expected_extension, expected_release = read(source)
    actual, extension, release = read(str(compressed) if as_string else compressed)
    pdt.assert_frame_equal(actual, expected)
    assert extension == expected_extension == source.suffix.lstrip('.')
    assert release == expected_release == RELEASES.dr3
    assert set(tmp_path.iterdir()) == {compressed}


@pytest.mark.parametrize('source', INPUT_FILES, ids=['csv', 'ecsv', 'fits', 'xml-plain', 'xml-binary'])
def test_gzip_release_mismatch(source, tmp_path):
    compressed = compress(source, tmp_path / (source.name + '.gz'))
    with pytest.raises(ValueError, match="selected release is 'dr4'.*identified as 'dr3'"):
        InputReader(compressed, convert, truncation=False, disable_info=True, release='dr4').read()


@pytest.mark.parametrize('source', INPUT_FILES[:4], ids=['csv', 'ecsv', 'fits', 'xml'])
def test_gzip_default_output_format(source, tmp_path):
    compressed = compress(source, tmp_path / (source.name + '.gz'))
    convert(compressed, output_path=tmp_path, output_file='converted', disable_info=True)
    assert (tmp_path / ('converted' + source.suffix)).is_file()
    assert not list(tmp_path.glob('converted*.gz'))


def test_unsupported_gzip_format(tmp_path):
    compressed = tmp_path / 'spectra.unknown.gz'
    with gzip.open(compressed, 'wb') as stream:
        stream.write(b'not a supported format')
    with pytest.raises(InvalidExtensionError):
        GenericParser().parse_file(compressed, disable_info=True)
