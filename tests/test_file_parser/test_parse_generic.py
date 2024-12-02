import pytest
from gaiaxpy.file_parser.parse_generic import _get_file_extension, GenericParser, InvalidExtensionError

from tests.files.paths import mini_csv_file, mini_fits_file, mini_xml_file


@pytest.fixture
def parser():
    yield GenericParser()


@pytest.mark.parametrize('file,extension', [[mini_csv_file, 'csv'], [mini_fits_file, 'fits'], [mini_xml_file, 'xml']])
def test_get_valid_extensions(file, extension):
    assert _get_file_extension(file) == extension


def test_get_no_extension():
    assert _get_file_extension('path/file') == ''


def test_get_directory():
    # Managing directories is not necessary because they return '' which is an invalid extension
    assert _get_file_extension('path/file/') == ''


def test_get_parser_error(parser):
    pytest.raises(InvalidExtensionError, parser.get_parser, '')


@pytest.mark.parametrize('extension,function', [['csv', '_parse_csv'], ['fits', '_parse_fits'], ['xml', '_parse_xml']])
def test_get_parser_extensions(parser, extension, function):
    assert parser.get_parser(extension) == getattr(parser, function)
