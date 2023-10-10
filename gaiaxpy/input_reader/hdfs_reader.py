import subprocess

from hdfs import InsecureClient
from hdfs.ext.avro import AvroReader

from gaiaxpy.input_reader.file_reader import FileReader


class HDFSReader(FileReader):

    def __init__(self, file_parser_selector, file, additional_columns=None, selector=None, disable_info=False):
        self.address, self.file, self.port = self.split_cluster_path(file)
        client = InsecureClient(f'{self.address}:{self.port}')
        with AvroReader(client, self.file) as reader:
            super().__init__(file_parser_selector, reader, additional_columns, selector, disable_info)

    def split_cluster_path(self, file_path, expected_protocol='http', p_sep='://'):
        def get_namenode():
            command = ['hdfs', 'getconf', '-confKey', 'dfs.namenode.http-address']
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
            output, error = process.communicate()
            process.wait()
            if process.returncode != 0:
                raise Exception(f"Failed to execute command '{command}': {error}")
            return output.decode('utf-8').split(':')[1]

        def modify_protocol(_given_protocol, _expected_protocol, _file_path):
            if _given_protocol != _expected_protocol:
                return _expected_protocol + _file_path[len(_given_protocol):]

        def process_address_and_port(_file_path, _protocol_split_index):
            address_and_port = _file_path[:_protocol_split_index]
            split_index_port = address_and_port.find(':', len(f'{expected_protocol}{p_sep}'))
            _address, _port = address_and_port[:split_index_port], address_and_port[split_index_port:]
            expected_port = get_namenode()
            if str(_port) != str(expected_port):
                _port = expected_port
            return _address, _port

        file_path = modify_protocol(file_path[:file_path.find(p_sep)], expected_protocol, file_path)
        protocol_split_index = file_path.find('/', len(f'{expected_protocol}{p_sep}'))
        if protocol_split_index == -1:
            raise ValueError('Input path has got a different format than expected.')
        else:
            address, port = process_address_and_port(file_path, protocol_split_index)
            file = file_path[protocol_split_index:]
            return address, file, port
