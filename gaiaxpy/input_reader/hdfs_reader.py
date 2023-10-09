import subprocess
from os.path import splitext

import pandas as pd
from hdfs.ext.avro import AvroReader

from gaiaxpy.core.generic_functions import standardise_extension, array_to_symmetric_matrix
from gaiaxpy.core.input_validator import check_column_overwrite
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.cast import _cast
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.file_reader import covariance_extensions
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, COV_INPUT_COLUMNS, CORR_INPUT_COLUMNS

from hdfs import InsecureClient

from gaiaxpy.spectrum.utils import get_covariance_matrix


class HDFSReader(object):

    def __init__(self, file_parser_selector, file_path, additional_columns=None, selector=None, disable_info=False):
        self.fps = file_parser_selector
        self.address, self.file, self.port = self.split_cluster_path(file_path)
        self.file_extension = standardise_extension(splitext(self.file)[1])
        self.additional_columns = dict() if additional_columns is None else additional_columns
        self.selector = selector
        self.disable_info = disable_info
        mandatory_columns = MANDATORY_INPUT_COLS.get(self.fps.function_name, list())
        style_columns = list()
        if mandatory_columns:
            # Files can contain covariances or correlations depending on the extension
            style_columns = COV_INPUT_COLUMNS if self.file_extension in covariance_extensions else CORR_INPUT_COLUMNS
        self.required_columns = mandatory_columns + style_columns
        self.requested_columns = self.required_columns
        if self.additional_columns:
            check_column_overwrite(additional_columns, self.required_columns)
            self.requested_columns = self.required_columns + self.get_extra_columns_from_extension()

    def split_cluster_path(self, file_path, expected_protocol = 'http', psep='://'):
        def get_namenode():
            command = ['hdfs', 'getconf', '-confKey', 'dfs.namenode.http-address']
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
            output, error = process.communicate()
            process.wait()
            if process.returncode != 0:
                raise Exception(f"Failed to execute command '{command}': {error}")
            return output.decode('utf-8').split(':')[1]

        actual_protocol = file_path[:file_path.find(psep)]
        if actual_protocol != expected_protocol:
            file_path = expected_protocol + file_path[len(actual_protocol):]
        # Find the index of the first '/' after 'http://'
        split_index = file_path.find('/', len(f'{expected_protocol}{psep}'))
        if split_index != -1:
            # Split the string into two parts
            address_and_port = file_path[:split_index]
            address, port = address_and_port.split(':')
            expected_port = get_namenode()
            if str(port) != str(expected_port):
                # TODO: Raise warning
                port = expected_port
            file = file_path[split_index:]
            return address, file, port
        else:
            raise ValueError('Input path different to expected.')

    def get_extra_columns_from_extension(self):
        if self.file_extension == 'avro':
            return [c for c in self.additional_columns.keys() if c not in self.required_columns]
        else:
            raise ValueError('Only AVRO files are allowed at the moment.')

    def read(self):
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
        additional_columns = self.additional_columns
        selector = self.selector
        client = InsecureClient(f'{self.address}:{self.port}')
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
