"""Read continuous mean spectra stored as BP/RP basis coefficients.

Tabular inputs provide coefficient errors and packed correlations.
The parser expands selected matrices and adds ``bp_covariance_matrix``
and ``rp_covariance_matrix`` columns for use by later calculations.
"""

import numpy as np
import pandas as pd
from fastavro import __version__ as fa_version
from hdfs import InsecureClient
from hdfs.ext.avro import AvroReader
from packaging import version
from requests.exceptions import ConnectionError

from gaiaxpy.core.generic_functions import array_to_symmetric_matrix, rename_with_required
from .avro_utils import _csv_to_avro_map, _get_from_dict
from .cast import _cast
from .parse_generic import GenericParser
from ..core.custom_errors import SelectorNotImplementedError
from ..core.satellite import BANDS
from ..spectrum.utils import get_covariance_matrix

# Columns that contain arrays (as strings)
array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'rp_coefficients', 'rp_coefficient_errors']
# Pairs of the form (matrix_size (N), values_to_put_in_matrix) for columns that contain matrices as strings
matrix_columns = [('bp_n_parameters', 'bp_coefficient_correlations'),
                  ('rp_n_parameters', 'rp_coefficient_correlations')]


class InternalContinuousParser(GenericParser):
    """Read internally calibrated continuous mean spectra and their covariances.

    CSV, ECSV, FITS and XML/VOTable use the shared readers.
    """

    def __init__(self, requested_columns=None, additional_columns=None, selector=None, **kwargs):
        """Set the required columns, additional fields and Avro record selector.

        Args:
            requested_columns (list[str] or None): Columns to read. None or an
                empty list reads all columns in tabular formats. Avro requires an
                explicit list using the tabular names from ``prepare_keys_map``.
            additional_columns (dict or None): Output names mapped to input key
                lists. Tabular inputs use one-element lists containing the input
                column name; Avro lists may follow nested keys. Defaults to None.
            selector (callable or None): Predicate applied to raw Avro records.
                Records are kept when it returns True. Tabular formats reject a
                non-None selector. Defaults to None.
            **kwargs: ``optional_columns`` lists columns to include if present.
                ``address`` and ``port`` configure access to Avro files over HDFS
                through its HTTP interface.

        Notes:
            A column selection must include the fields needed to construct BP/RP
            covariance matrices, such as coefficient errors, correlations and
            standard deviations for correlation-based input.
        """
        super().__init__()
        self.optional_columns = kwargs.get('optional_columns', [])
        self.additional_columns = dict() if additional_columns is None else additional_columns
        self.requested_columns = requested_columns
        self.selector = selector
        if kwargs:
            self.address = kwargs.get('address', None)
            self.port = kwargs.get('port', None)

    def __add_covariance_matrices(self, df):
        """Add BP and RP covariance-matrix columns to the supplied DataFrame.

        Existing covariance matrices are reused. Otherwise, the covariance is
        obtained from coefficient covariances or from correlations, errors and
        standard deviations using :func:`gaiaxpy.spectrum.utils.get_covariance_matrix`.
        Missing-band values follow that helper's handling. Return the updated table.
        """
        for band in BANDS:
            df[f'{band}_covariance_matrix'] = [get_covariance_matrix(row, band) for row in df.itertuples(index=False)]
        return df

    def __parse_dataframe_file(self, parse_method, input_file, selector_type,
                               _array_columns=None, _matrix_columns=None, _usecols=None):
        """Read a tabular format, add covariances and rename additional columns.

        Use the parser's array and matrix defaults when their arguments are None.
        A non-empty ``_usecols`` overrides ``requested_columns``. Optional columns
        are included when available by the shared format reader. A non-None
        selector raises ``SelectorNotImplementedError`` for the named format.
        """
        if self.selector is not None:
            raise SelectorNotImplementedError(selector_type)
        if _matrix_columns is None:
            _matrix_columns = matrix_columns
        if _array_columns is None:
            _array_columns = array_columns
        _usecols = _usecols if _usecols else self.requested_columns
        df = parse_method(input_file, _array_columns=_array_columns, _matrix_columns=_matrix_columns,
                          _usecols=_usecols)
        df = self.__add_covariance_matrices(df)
        return rename_with_required(df, self.additional_columns)

    def _parse_ecsv(self, ecsv_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """Read continuous ECSV spectra and add BP/RP covariance columns.

        Arguments follow ``_parse_csv``. Arrays and metadata are read from
        the ECSV header. Floating-point values use float64 precision,
        and the original type declarations are retained in DataFrame attrs.
        Additional columns are renamed as for other tabular inputs.
        A non-None selector raises ``SelectorNotImplementedError``.
        """
        return self.__parse_dataframe_file(super()._parse_ecsv, ecsv_file, 'ECSV', _array_columns,
                                           _matrix_columns, _usecols)

    def _parse_csv(self, csv_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """Read continuous-spectrum data from CSV and add covariance matrices.

        Args:
            csv_file (str, pathlib.Path or file-like): Input filename or readable
                stream supported by the format reader.
            _array_columns (list[str] or None): Columns to convert to NumPy arrays. None uses the
                BP/RP coefficient and coefficient-error columns.
            _matrix_columns (list[tuple[str, str]] or None): Pairs of size-column
                and packed-value-column names. None expands the BP/RP coefficient
                correlations using their corresponding parameter counts.
            _usecols (list[str] or None): Non-empty column selection overriding
                ``requested_columns``. Available optional columns are included.

        Returns:
            pandas.DataFrame: Selected data with the requested matrix conversions,
            BP/RP covariance columns and renamed additional columns.
            Matrix expansion can be disabled with an empty ``_matrix_columns`` list.

        Raises:
            SelectorNotImplementedError: A record selector was supplied for this
                format. Selectors are supported only by the Avro reader. Support
                for reading Avro files is intended solely for internal use. The
                Archive does not distribute files in this format.

        """
        return self.__parse_dataframe_file(super()._parse_csv, csv_file, 'E/CSV', _array_columns,
                                           _matrix_columns, _usecols)

    def _parse_fits(self, fits_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """Read continuous-spectrum data from FITS and add covariance matrices.

        Args:
            fits_file (str, pathlib.Path or file-like): Input filename or readable
                stream supported by the format reader.
            _array_columns (list[str] or None): Accepted for compatibility; Astropy reads native arrays.
            _matrix_columns (list[tuple[str, str]] or None): Pairs of size-column
                and packed-value-column names. None expands the BP/RP coefficient
                correlations using their corresponding parameter counts.
            _usecols (list[str] or None): Non-empty column selection overriding
                ``requested_columns``. Available optional columns are included.

        Returns:
            pandas.DataFrame: Selected data with the requested matrix conversions,
            BP/RP covariance columns and renamed additional columns.
            Matrix expansion can be disabled with an empty ``_matrix_columns`` list.

        Raises:
            SelectorNotImplementedError: A record selector was supplied for this
                format. Selectors are supported only by the Avro reader. Support
                for reading Avro files is intended solely for internal use. The
                Archive does not distribute files in this format.
        """
        return self.__parse_dataframe_file(super()._parse_fits, fits_file, 'FITS', _array_columns,
                                           _matrix_columns, _usecols)

    def _parse_xml(self, xml_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """Read continuous-spectrum data from XML/VOTable and add covariance matrices.

        Args:
            xml_file (str, pathlib.Path or file-like): Input filename or readable
                stream supported by the format reader.
            _array_columns (list[str] or None): Accepted for compatibility; Astropy reads native arrays.
            _matrix_columns (list[tuple[str, str]] or None): Pairs of size-column
                and packed-value-column names. None expands the BP/RP coefficient
                correlations using their corresponding parameter counts.
            _usecols (list[str] or None): Non-empty column selection overriding
                ``requested_columns``. Available optional columns are included.

        Returns:
            pandas.DataFrame: Selected data with the requested matrix conversions,
            BP/RP covariance columns and renamed additional columns.
            Matrix expansion can be disabled with an empty ``_matrix_columns`` list.

        Raises:
            SelectorNotImplementedError: A record selector was supplied for this
                format. Selectors are supported only by the Avro reader. Support
                for reading Avro files is intended solely for internal use. The
                Archive does not distribute files in this format.
        """
        return self.__parse_dataframe_file(super()._parse_xml, xml_file, 'XML', _array_columns,
                                           _matrix_columns, _usecols)

    @staticmethod
    def __process_avro_record(record, keys_map, filtered_keys, optional_keys=()):
        """Extract selected fields from one Avro record using a key-path mapping.
        Support for reading Avro files is intended solely for internal use. The
        Archive does not distribute files in this format.

        List values become NumPy arrays. Missing optional keys are skipped;
        missing required keys raise KeyError. A lookup through a non-indexable
        value follows the NaN handling in ``_get_from_dict``.
        """
        result = {}
        for key in list(filtered_keys) + [key for key in optional_keys if key not in filtered_keys]:
            try:
                value = _get_from_dict(record, keys_map[key])
            except KeyError:
                if key in optional_keys:
                    continue
                raise
            result[key] = np.array(value) if isinstance(value, list) else value
        return result

    def __get_records_up_to_1_4_7(self, avro_file, additional_columns, selector, **kwargs):
        """Yield selected local records for fastavro versions up to and including 1.4.7.
        Support for reading Avro files is intended solely for internal use. The Archive
        does not distribute files in this format.

        Apply the selector to raw records, then extract requested and optional
        fields. A supplied HDFS address raises ValueError because this reader
        supports local filenames only.
        """
        address = kwargs.get('address', None)
        if address:
            raise ValueError('HDFS access not implemented for fastavro versions older than 1.4.7.')
        from fastavro import reader
        f = open(avro_file, 'rb')
        _avro_keys_map = InternalContinuousParser.prepare_keys_map(additional_columns)
        filtered_keys = list(filter(lambda key: key in self.requested_columns, _avro_keys_map.keys()))
        avro_reader = reader(f)
        avro_reader = avro_reader if selector is None else filter(selector, avro_reader)
        record = next(avro_reader)
        while record:
            try:
                current_record = InternalContinuousParser.__process_avro_record(record, _avro_keys_map, filtered_keys,
                                                                                self.optional_columns)
                yield current_record
            except KeyError:
                raise KeyError("Keys in the input file don't match the expected ones.")
            try:
                record = next(avro_reader)
            except StopIteration:
                f.close()
                break

    def __get_records_later_than_1_4_7(self, avro_file, additional_columns, selector, **kwargs):
        """Yield selected local or HDFS records for fastavro versions newer than 1.4.7.
        Support for reading Avro files is intended solely for internal use. The Archive
        does not distribute files in this format.

        Use block reading for local files, or an HDFS client when ``address`` is
        provided in ``kwargs``. Apply the selector before extracting fields.
        """

        def __yield_local_records(_avro_file):
            """Yield raw records from each block in a local Avro file."""
            from fastavro import block_reader
            with open(_avro_file, 'rb') as fo:
                for block in block_reader(fo):
                    for rec in block:
                        yield rec

        def __yield_remote_records(_avro_file):
            """Yield raw Avro records through the configured HDFS client."""
            client = InsecureClient(f'{address}:{port}')
            with AvroReader(client, _avro_file) as reader:
                for _r in reader:
                    yield _r

        address = kwargs.get('address', None)
        port = kwargs.get('port', None)
        records = __yield_remote_records(avro_file) if address else __yield_local_records(avro_file)
        records = records if selector is None else filter(selector, records)
        _avro_keys_map = InternalContinuousParser.prepare_keys_map(additional_columns)
        filtered_keys = list(filter(lambda key: key in self.requested_columns, _avro_keys_map.keys()))
        for record in records:
            yield InternalContinuousParser.__process_avro_record(record, _avro_keys_map, filtered_keys,
                                                                 self.optional_columns)

    @staticmethod
    def prepare_keys_map(additional_columns):
        """Combine the standard Avro field mapping with additional column mappings.
        Support for reading Avro files is intended solely for internal use. The
        Archive does not distribute files in this format.

        Args:
            additional_columns (dict): Additional output column names mapped to
                lists of keys in the Avro record. Use an empty dictionary when no
                extra columns are needed.

        Returns:
            dict: A copy of the standard mapping extended with the supplied
            additional columns.

        Raises:
            ValueError: An additional column would replace a standard mapped name.
        """
        _avro_keys_map = _csv_to_avro_map.copy()
        intersection_keys = [key for key in _avro_keys_map.keys() if key in additional_columns.keys()]
        if intersection_keys:
            raise ValueError('Additional columns will overwrite an already existing key. This is not allowed.'
                             f' Keys are: {",".join(intersection_keys)}')
        if additional_columns is not None:
            _avro_keys_map.update(additional_columns)
        return _avro_keys_map

    def _parse_avro(self, avro_file):
        """Read nested Avro records and add BP/RP covariance-matrix columns.
        Support for reading Avro files is intended solely for internal use.
        The Archive does not distribute files in this format.

        Args:
            avro_file (str or pathlib.Path): Local filename, or an HDFS file path
                when ``address`` and ``port`` have been configured. This reader
                expects a filename rather than an open input stream.

        Returns:
            pandas.DataFrame: Requested and available optional fields, with lists
            converted to arrays, packed coefficient covariances expanded to square
            matrices and recognised column types standardised.

        Raises:
            ValueError: Additional column names conflict with standard names, or
                HDFS access is requested with fastavro 1.4.7 or earlier.
            KeyError: Required mapped fields are missing from the records or from
                the resulting table.
            requests.exceptions.ConnectionError: HDFS connections still fail after
                ten attempts.

        Notes:
            ``requested_columns`` must include the parameter counts, coefficient
            covariances and other fields needed by later processing. The selector
            receives raw Avro records before field extraction. Optional fields
            missing from a record are skipped.
        """

        def __records_to_df(max_conn_retries=10, **_records_arguments):
            """Build a DataFrame, retrying requests connection errors up to the given limit.

            Other exceptions are raised immediately. Raise a connection error when
            no attempt succeeds.
            """
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
            __get_records = self.__get_records_up_to_1_4_7
        elif version.parse(fa_version) > version.parse('1.4.7'):
            __get_records = self.__get_records_later_than_1_4_7
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
            df[values_column] = [array_to_symmetric_matrix(array, size) for array, size in zip(df[values_column],
                                                                                               df[size_column])]
        df = self.__add_covariance_matrices(df)
        return _cast(df)
