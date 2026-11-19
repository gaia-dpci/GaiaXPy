"""Configure the internal Avro reader for files stored on HDFS.
Support for HDFS and Avro files is intended solely for internal use.
The Archive does not distribute Avro files."""

import subprocess
from os.path import splitext

from gaiaxpy.core.custom_errors import ExtensionNotImplementedError
from gaiaxpy.core.generic_functions import standardise_extension
from gaiaxpy.input_reader.file_reader import FileReader


def get_http_port():
    """Read the NameNode HTTP port using the installed hdfs command.

    Returns:
        str: Port extracted from dfs.namenode.http-address.

    Raises:
        Exception: The hdfs configuration command returns a non-zero status.
        FileNotFoundError: The hdfs executable is unavailable.
    """
    command = ['hdfs', 'getconf', '-confKey', 'dfs.namenode.http-address']
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    output, error = process.communicate()
    process.wait()
    if process.returncode != 0:
        raise Exception(f"Failed to execute command '{command}': {error}")
    return output.decode('utf-8').split(':')[1]


def split_cluster_path(file_path, expected_protocol='http', p_sep='://'):
    """Separate an HDFS URL into its service address, file path and HTTP port.

    Args:
        file_path (str): URL containing a service address and file path.
        expected_protocol (str): Protocol used in the returned service address.
        p_sep (str): Separator between protocol and address; defaults to '://'.

    Returns:
        tuple[str, str, str]: Service address, absolute file path and configured
        NameNode HTTP port. The protocol is replaced when necessary, and the
        port comes from the local hdfs configuration.

    Raises:
        ValueError: No file-path separator follows the service address.

    Notes:
        Resolving the port requires the hdfs command and its local configuration.
    """

    def process_address_and_port(_file_path, _protocol_split_index):
        """Split the service address and use the configured NameNode HTTP port."""
        expected_port = get_http_port()
        address_and_port = _file_path[:_protocol_split_index]
        split_index_port = address_and_port.find(':', len(f'{expected_protocol}{p_sep}'))
        if split_index_port != -1:
            _address, _port = address_and_port[:split_index_port], address_and_port[split_index_port:]
            if str(_port) != str(expected_port):
                _port = expected_port
            return _address, _port
        else:
            return address_and_port, expected_port

    def modify_protocol(_given_protocol, _expected_protocol, _file_path):
        """Replace the URL protocol when it differs from the expected protocol."""
        if _given_protocol != _expected_protocol:
            return _expected_protocol + _file_path[len(_given_protocol):]
        return _file_path

    file_path = modify_protocol(file_path[:file_path.find(p_sep)], expected_protocol, file_path)
    protocol_split_index = file_path.find('/', len(f'{expected_protocol}{p_sep}'))
    if protocol_split_index == -1:
        raise ValueError('Input path has got a different format than expected.')
    else:
        address, port = process_address_and_port(file_path, protocol_split_index)
        file = file_path[protocol_split_index:]
        return address, file, port


class HDFSReader(FileReader):
    """Configure FileReader for an Avro file on an HDFS service.

    This internal reader requires the hdfs command and an Avro-capable parser.
    """

    def __init__(self, file_parser_selector, file, truncation, additional_columns=None, selector=None,
                 disable_info=False):
        """Resolve the service connection and configure the Avro file reader.
        Support for HDFS and Avro files is intended solely for internal use.
        The Archive does not distribute Avro files.

        Args:
            file_parser_selector (FileParserSelector): Parser factory for the operation.
            file (str): HDFS URL containing the service address and file path.
            truncation (bool): Whether subsequent calculations use the recommended
                number of basis functions for each source and photometer. When True,
                this reader includes bp_n_relevant_bases and rp_n_relevant_bases.
                When False, calculations use all available basis functions.
            additional_columns (dict or None): Extra input-field mappings.
            selector (object or None): Selection passed to the parser.
            disable_info (bool): Suppress routine reading messages.

        Raises:
            ExtensionNotImplementedError: The file extension is not Avro.
        """
        address, file_path, port = split_cluster_path(file)
        extension = standardise_extension(splitext(file_path)[1]).lower()
        if standardise_extension(splitext(file_path)[1]).lower() != 'avro':
            raise ExtensionNotImplementedError(extension)
        super().__init__(file_parser_selector, file_path, truncation, additional_columns, selector, disable_info,
                         address=address, port=port)
