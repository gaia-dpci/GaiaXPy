import pytest
from gaiaxpy.input_reader.hdfs_reader import split_cluster_path


@pytest.mark.parametrize(
    "dir_path, expected_address, expected_file, expected_port",
    [
        ('hdfs://namenode:port/path/to/dir', 'http://namenode', '/path/to/dir', 9870),
        ('http://namenode:port/path/to/dir', 'http://namenode', '/path/to/dir', 9870),
        ('http://namenode/path/to/dir', 'http://namenode', '/path/to/dir', 9870)
    ]
)
def test_process_address_and_port_with_mock(mocker, dir_path, expected_address, expected_file, expected_port):
    # Set up mock for get_http_port()
    mocker.patch('gaiaxpy.input_reader.hdfs_reader.get_http_port', return_value=9870)

    address, file, port = split_cluster_path(dir_path)

    assert address == expected_address
    assert file == expected_file
    assert port == expected_port
