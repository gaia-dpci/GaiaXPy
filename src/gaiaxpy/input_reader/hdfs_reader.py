import subprocess
from os.path import splitext

from gaiaxpy.core.custom_errors import ExtensionNotImplementedError
from gaiaxpy.core.generic_functions import standardise_extension
from gaiaxpy.input_reader.file_reader import FileReader


def get_http_port():
    command = ['hdfs', 'getconf', '-confKey', 'dfs.namenode.http-address']
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    output, error = process.communicate()
    process.wait()
    if process.returncode != 0:
        raise Exception(f"Failed to execute command '{command}': {error}")
    return output.decode('utf-8').split(':')[1]


def split_cluster_path(file_path, expected_protocol='http', p_sep='://'):
    def process_address_and_port(_file_path, _protocol_split_index):
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

    def __init__(self, file_parser_selector, file, truncation, additional_columns=None, selector=None,
                 disable_info=False):
        address, file_path, port = split_cluster_path(file)
        extension = standardise_extension(splitext(file_path)[1]).lower()
        if standardise_extension(splitext(file_path)[1]).lower() != 'avro':
            raise ExtensionNotImplementedError(extension)
        super().__init__(file_parser_selector, file_path, truncation, additional_columns, selector, disable_info,
                         address=address, port=port)
