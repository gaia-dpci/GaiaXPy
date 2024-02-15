"""
parse_internal_continuous.py
====================================
Module to parse input files containing internally calibrated continuous spectra.
"""

import numpy as np
import pandas as pd
from fastavro import __version__ as fa_version
from hdfs import InsecureClient
from hdfs.ext.avro import AvroReader
from packaging import version
from requests.exceptions import ConnectionError

from gaiaxpy.core.generic_functions import array_to_symmetric_matrix, rename_with_required
from .cast import _cast
from .parse_generic import GenericParser
from .utils import _csv_to_avro_map, _get_from_dict
from ..core.custom_errors import SelectorNotImplementedError
from ..core.satellite import BANDS
from ..spectrum.utils import get_covariance_matrix

# Columns that contain arrays (as strings)
array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'rp_coefficients', 'rp_coefficient_errors']
# Pairs of the form (matrix_size (N), values_to_put_in_matrix) for columns that contain matrices as strings
matrix_columns = [('bp_n_parameters', 'bp_coefficient_correlations'),
                  ('rp_n_parameters', 'rp_coefficient_correlations')]


class InternalContinuousParser(GenericParser):
    """
    Parser for internally calibrated continuous spectra.
    """

    def __init__(self, requested_columns=None, additional_columns=None, selector=None, **kwargs):
        super().__init__()
        self.additional_columns = dict() if additional_columns is None else additional_columns
        self.requested_columns = requested_columns
        self.selector = selector
        if kwargs:
            self.address = kwargs.get('address', None)
            self.port = kwargs.get('port', None)

    def _parse_csv(self, csv_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """
        Parse the input CSV file and store the result in a pandas DataFrame if it contains internally calibrated
            continuous spectra.

        Args:
            csv_file (str): Path to a CSV file.
            _array_columns (list): List of columns in the file that contain arrays as strings.
            _matrix_columns (list of tuples): List of tuples where the first element is the number of rows/columns of a
                square matrix which values are those contained in the second element of the tuple.
            _usecols (list): Columns to read.

        Returns:
            DataFrame: Pandas DataFrame representing the CSV file.
        """
        if self.selector is not None:
            raise SelectorNotImplementedError('E/CSV')
        if _matrix_columns is None:
            _matrix_columns = matrix_columns
        if _array_columns is None:
            _array_columns = array_columns
        _usecols = _usecols if _usecols else self.requested_columns
        df = super()._parse_csv(csv_file, _array_columns=_array_columns, _matrix_columns=_matrix_columns,
                                _usecols=_usecols)
        for band in BANDS:
            df[f'{band}_covariance_matrix'] = df.apply(get_covariance_matrix, axis=1, args=(band,))
        df = rename_with_required(df, self.additional_columns)
        return df

    def _parse_fits(self, fits_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """
        Parse the input FITS file and store the result in a pandas DataFrame if it contains internally calibrated
            continuous spectra.

        Args:
            fits_file (str): Path to a FITS file.
            _array_columns (list): List of columns in the file that contain arrays as strings.
            _matrix_columns (list of tuples): List of tuples where the first element is the number of rows/columns of a
                square matrix which values are those contained in the second element of the tuple.
            _usecols (list): Columns to read.

        Returns:
            DataFrame: Pandas DataFrame representing the FITS file.
        """
        if self.selector is not None:
            raise SelectorNotImplementedError('FITS')
        if _matrix_columns is None:
            _matrix_columns = matrix_columns
        if _array_columns is None:
            _array_columns = array_columns
        _usecols = _usecols if _usecols else self.requested_columns
        df = super()._parse_fits(fits_file, _array_columns=_array_columns, _matrix_columns=_matrix_columns,
                                 _usecols=_usecols)
        for band in BANDS:
            df[f'{band}_covariance_matrix'] = df.apply(get_covariance_matrix, axis=1, args=(band,))
        df = rename_with_required(df, self.additional_columns)
        return df

    def _parse_xml(self, xml_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """
        Parse the input XML file and store the result in a pandas DataFrame.

        Args:
            xml_file (str): Path to an XML file.
            _array_columns (list): List of columns in the file that contain arrays as strings.
            _matrix_columns (list of tuples): List of tuples where the first element is the number of rows/columns of a
                square matrix which values are those contained in the second element of the tuple.
            _usecols (list): Columns to read.

        Returns:
            DataFrame: A pandas DataFrame representing the XML file.
        """
        if self.selector is not None:
            raise SelectorNotImplementedError('XML')
        if _matrix_columns is None:
            _matrix_columns = matrix_columns
        if _array_columns is None:
            _array_columns = array_columns
        _usecols = _usecols if _usecols else self.requested_columns
        df = super()._parse_xml(xml_file, _array_columns=_array_columns, _matrix_columns=_matrix_columns,
                                _usecols=_usecols)
        for band in BANDS:
            df[f'{band}_covariance_matrix'] = df.apply(get_covariance_matrix, axis=1, args=(band,))
        df = rename_with_required(df, self.additional_columns)
        return df

    @staticmethod
    def __process_avro_record(record, additional_columns=None):
        _avro_keys_map = _csv_to_avro_map.copy()
        intersection_keys = [key for key in _avro_keys_map.keys() if key in additional_columns.keys()]
        if intersection_keys:
            raise ValueError('Additional columns will overwrite an already existing key. This is not allowed.'
                             f' Keys are: {",".join(intersection_keys)}')
        if additional_columns is not None:
            _avro_keys_map.update(additional_columns)
        return {key: np.array(_get_from_dict(record, _avro_keys_map[key])) if isinstance(
            _get_from_dict(record, _avro_keys_map[key]), list) else _get_from_dict(
            record, _avro_keys_map[key]) for key in _avro_keys_map.keys()}

    @staticmethod
    def __get_records_up_to_1_4_7(avro_file, additional_columns, selector, **kwargs):
        address = kwargs.get('address', None)
        if address:
            raise ValueError('HDFS access not implemented for fastavro versions older than 1.4.7.')
        from fastavro import reader
        f = open(avro_file, 'rb')
        avro_reader = reader(f)
        avro_reader = avro_reader if selector is None else filter(selector, avro_reader)
        record = avro_reader.next()
        while record:
            try:
                current_record = InternalContinuousParser.__process_avro_record(record, additional_columns)
                yield current_record
            except KeyError:
                raise KeyError("Keys in the input file don't match the expected ones.")
            try:
                record = avro_reader.next()
            except StopIteration:
                f.close()
                break

    @staticmethod
    def __get_records_later_than_1_4_7(avro_file, additional_columns, selector, **kwargs):
        def __yield_local_records(_avro_file):
            from fastavro import block_reader
            with open(_avro_file, 'rb') as fo:
                for block in block_reader(fo):
                    for rec in block:
                        yield rec

        def __yield_remote_records(_avro_file):
            client = InsecureClient(f'{address}:{port}')
            with AvroReader(client, _avro_file) as reader:
                for record in reader:
                    yield record

        address = kwargs.get('address', None)
        port = kwargs.get('port', None)
        records = __yield_remote_records(avro_file) if address else __yield_local_records(avro_file)
        records = records if selector is None else filter(selector, records)
        for record in records:
            yield InternalContinuousParser.__process_avro_record(record, additional_columns)

    def _parse_avro(self, avro_file):
        """
        Parse the input AVRO file and return the result as a Pandas DataFrame.

        Args:
            avro_file (str): Path to an AVRO file.

        Returns:
            DataFrame: Pandas DataFrame representing the AVRO file.
        """

        def __records_to_df(max_conn_retries=10, **_records_arguments):
            retries = 0
            while retries < max_conn_retries:
                try:
                    _df = pd.DataFrame(__get_records(**_records_arguments))
                    break
                except ConnectionError:
                    retries += 1
            else:
                raise ConnectionError(
                    f'Failed to connect to HDFS after {max_conn_retries} attempts for file {avro_file}.')
            return _df

        if version.parse(fa_version) <= version.parse('1.4.7'):
            __get_records = InternalContinuousParser.__get_records_up_to_1_4_7
        elif version.parse(fa_version) > version.parse('1.4.7'):
            __get_records = InternalContinuousParser.__get_records_later_than_1_4_7
        else:
            raise ValueError(f'Fastavro version {fa_version} may not have been parsed properly.')
        records_arguments = {
            'avro_file': avro_file,
            'additional_columns': self.additional_columns,
            'selector': self.selector
        }
        if hasattr(self, 'address') and hasattr(self, 'port'):
            records_arguments['address'] = self.address
            records_arguments['port'] = self.port
        df = __records_to_df(**records_arguments)
        # Pairs of the form (matrix_size (N), values_to_put_in_matrix)
        to_matrix_columns = [('bp_n_parameters', 'bp_coefficient_covariances'),
                             ('rp_n_parameters', 'rp_coefficient_covariances')]
        for size_column, values_column in to_matrix_columns:
            df[values_column] = df.apply(lambda row: array_to_symmetric_matrix(row[values_column], row[size_column]),
                                         axis=1)
        for band in BANDS:
            df[f'{band}_covariance_matrix'] = df.apply(get_covariance_matrix, axis=1, args=(band,))
        return _cast(df)
