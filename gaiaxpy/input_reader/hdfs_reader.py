import subprocess

import pandas as pd
from hdfs import InsecureClient
from hdfs.ext.avro import AvroReader

from gaiaxpy.core.generic_functions import array_to_symmetric_matrix, _warning
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.cast import _cast
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.file_reader import FileReader
from gaiaxpy.spectrum.utils import get_covariance_matrix


class HDFSReader(FileReader):

    def __init__(self, file_parser_selector, file, additional_columns=None, selector=None, disable_info=False):
        self.address, self.file, self.port = self.split_cluster_path(file)
        super().__init__(file_parser_selector, self.file, additional_columns, selector, disable_info)

    def split_cluster_path(self, file_path, expected_protocol='http', p_sep='://'):
        def get_namenode():
            command = ['hdfs', 'getconf', '-confKey', 'dfs.namenode.http-address']
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
            output, error = process.communicate()
            process.wait()
            if process.returncode != 0:
                raise Exception(f"Failed to execute command '{command}': {error}")
            return output.decode('utf-8').split(':')[1]

        def verify_protocol(_given_protocol, _expected_protocol, _file_path):
            if _given_protocol != _expected_protocol:
                _warning(f'Input protocol {_given_protocol.upper()} is different from expected protocol '
                         f'{_expected_protocol.upper()}. The protocol will be internally replaced.')
                return _expected_protocol + _file_path[len(_given_protocol):]

        def process_address_and_port(_file_path, _protocol_split_index):
            address_and_port = _file_path[:_protocol_split_index]
            split_index_port = address_and_port.find(':', len(f'{expected_protocol}{p_sep}'))
            _address, _port = address_and_port[:split_index_port], address_and_port[split_index_port:]
            expected_port = get_namenode()
            if str(_port) != str(expected_port):
                _warning(f'Input port {_port} is different from expected HTTP port {expected_port}. '
                         f'The port will be replaced.')
                _port = expected_port
            return _address, _port

        file_path = verify_protocol(file_path[:file_path.find(p_sep)], expected_protocol, file_path)
        protocol_split_index = file_path.find('/', len(f'{expected_protocol}{p_sep}'))
        if protocol_split_index == -1:
            raise ValueError('Input path has got a different format than expected.')
        else:
            address, port = process_address_and_port(file_path, protocol_split_index)
            file = file_path[protocol_split_index:]
            return address, file, port

    def read(self):
        client = InsecureClient(f'{self.address}:{self.port}')

        def __get_records(_avro_file, _additional_columns, _selector):
            def __yield_records(_avro_file):
                with AvroReader(client, _avro_file) as reader:
                    _records = reader.content
                    for _record in _records:
                        yield _record

            records = __yield_records(self.file)
            records = records if _selector is None else filter(_selector, records)
            for record in records:
                yield InternalContinuousParser.__process_avro_record(record, _additional_columns)

        df = pd.DataFrame(__get_records(self.file, self.additional_columns, self.selector))
        # Pairs of the form (matrix_size (N), values_to_put_in_matrix)
        to_matrix_columns = [('bp_n_parameters', 'bp_coefficient_covariances'),
                             ('rp_n_parameters', 'rp_coefficient_covariances')]
        for size_column, values_column in to_matrix_columns:
            df[values_column] = df.apply(lambda row: array_to_symmetric_matrix(row[values_column], row[size_column]),
                                         axis=1)
        for band in BANDS:
            df[f'{band}_covariance_matrix'] = df.apply(get_covariance_matrix, axis=1, args=(band,))
        return _cast(df), self.file_extension
