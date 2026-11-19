import pandas.testing as pdt
import pytest

from gaiaxpy import convert
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.input_reader.input_reader import InputReader
from tests.files.continuous import (dr3_with_missing_bp_csv_file, dr3_with_missing_bp_ecsv_file,
                                    dr3_with_missing_bp_fits_file, dr3_with_missing_bp_xml_plain_file,
                                    dr3_with_missing_bp_xml_binary_file, dr3_zipped_raw_files,
                                    dr3_zipped_individual_files)

UNZIPPED_FILES = [dr3_with_missing_bp_csv_file, dr3_with_missing_bp_ecsv_file, dr3_with_missing_bp_fits_file,
                  dr3_with_missing_bp_xml_plain_file, dr3_with_missing_bp_xml_binary_file]

EXPECTED_EXTENSIONS = ['csv', 'ecsv', 'fits', 'xml', 'xml']


@pytest.mark.parametrize(
    ('zip_file', 'uncompressed_file', 'expected_extension'),
    list(zip(dr3_zipped_raw_files, UNZIPPED_FILES, EXPECTED_EXTENSIONS)),
    ids=['csv', 'ecsv', 'fits', 'xml-plain', 'xml-binary'],
)
def test_read_zipped_raw_file(zip_file, uncompressed_file, expected_extension):
    expected, _, _ = InputReader(uncompressed_file, convert, truncation=False, release=RELEASES.dr3).read()
    actual, extension, release = InputReader(zip_file, convert, truncation=False, release=RELEASES.dr3).read()

    pdt.assert_frame_equal(actual, expected)
    assert extension == expected_extension
    assert release == RELEASES.dr3


@pytest.mark.parametrize(('zip_file', 'uncompressed_file', 'expected_extension'),
                         list(zip(dr3_zipped_individual_files, UNZIPPED_FILES, EXPECTED_EXTENSIONS)),
                         ids=['csv', 'ecsv', 'fits', 'xml-plain', 'xml-binary'])
def test_read_zipped_individual_files(zip_file, uncompressed_file, expected_extension):
    expected, _, _ = InputReader(uncompressed_file, convert, truncation=False, release=RELEASES.dr3).read()
    actual, extension, release = InputReader(zip_file, convert, truncation=False, release=RELEASES.dr3).read()

    pdt.assert_frame_equal(actual, expected)
    assert extension == expected_extension
    assert release == RELEASES.dr3


@pytest.mark.parametrize('as_string', [False, True], ids=['path', 'str'])
def test_zip_path_types(as_string):
    zip_file = dr3_zipped_raw_files[0]
    input_value = str(zip_file) if as_string else zip_file

    data, extension, release = InputReader(input_value, convert, truncation=False, release=RELEASES.dr3).read()

    assert data['source_id'].tolist() == [5853498713190525696, 5405570973190252288, 5762406957886626816]
    assert extension == 'csv'
    assert release == RELEASES.dr3


@pytest.mark.parametrize('members, message', [
    ([('spectra/', '')], 'directory entry'),
    ([('notes.txt', 'not a table')], 'unsupported extension'),
    ([('source.csv', 'source_id\n1\n'), ('notes.txt', 'not a table')], 'unsupported extension'),
    ([('source.csv', 'source_id\n1\n'), ('spectra/', '')], 'directory entry'),
    ([('source.csv', 'source_id\n1\n'), ('source.fits', '')], "expected 'csv'"),
    ([('source.csv.gz', '')], 'unsupported extension'),
    ([('source', '')], 'unsupported extension'),
], ids=['directory', 'unsupported-only', 'unsupported-after-table', 'directory-after-table',
        'mixed-formats', 'gzip-member', 'no-extension'])
def test_invalid_members_are_rejected_before_parsing(tmp_path, mocker, members, message):
    from zipfile import ZipFile

    path = tmp_path / 'invalid.zip'
    with ZipFile(path, 'w') as archive:
        for name, content in members:
            archive.writestr(name, content)
    read = mocker.patch('gaiaxpy.input_reader.zip_reader.LocalFileReader.read')

    with pytest.raises(ValueError, match=message) as error:
        InputReader(path, convert, truncation=False, disable_info=True, release=RELEASES.dr3).read()

    assert repr(members[-1][0]) in str(error.value)
    read.assert_not_called()


def test_empty_zip_is_rejected(tmp_path):
    from zipfile import ZipFile

    path = tmp_path / 'empty.zip'
    with ZipFile(path, 'w'):
        pass
    with pytest.raises(ValueError, match='contains no supported input files'):
        InputReader(path, convert, truncation=False).read()


def test_invalid_zip_is_rejected(tmp_path):
    path = tmp_path / 'invalid.zip'
    path.write_text('not a ZIP file')
    with pytest.raises(ValueError, match='not a valid ZIP archive'):
        InputReader(path, convert, truncation=False).read()


@pytest.mark.parametrize('extension', ['csv', 'ecsv', 'fits', 'xml', 'avro'])
def test_member_extensions_are_case_insensitive(tmp_path, extension):
    from zipfile import ZipFile
    from gaiaxpy.input_reader.zip_reader import ZipReader

    path = tmp_path / 'same-format.zip'
    names = [f'first.{extension.upper()}', f'second.{extension}']
    with ZipFile(path, 'w') as archive:
        for name in names:
            archive.writestr(name, '')
    with ZipFile(path) as archive:
        members = ZipReader._get_data_members(archive)
    assert [member.filename for member, _ in members] == names
    assert [suffix for _, suffix in members] == [extension, extension]
