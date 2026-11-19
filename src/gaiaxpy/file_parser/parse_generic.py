"""Shared file readers, extension handling and gzip support for spectrum parsers."""

import gzip
from contextlib import nullcontext
from gzip import GzipFile
from pathlib import Path
from typing import Union

from gaiaxpy.core.generic_functions import array_to_symmetric_matrix, str_to_array, get_file_extension
from .cast import _cast
from ..core.generic_variables import VALID_EXTENSIONS
from ..core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from ..input_reader.required_columns import get_present_optional_columns


class InvalidExtensionError(ValueError):
    """Raised when a filename extension has no matching parser.

    The message lists GaiaXPy's recognised extensions. Individual parser
    classes may support only a subset of those formats.
    """

    def __init__(self, extension: str):
        """Create an error identifying an unsupported extension.

        Args:
            extension (str): Extension that could not be matched to a reader.
        """
        valid = ', '.join(VALID_EXTENSIONS)
        message = f'Extension of {extension} is not valid. Valid extensions are: {valid}.'
        Exception.__init__(self, message)


class GenericParser:
    """Read tabular spectrum data using the reader for its file format.

    Subclasses choose which columns contain arrays or matrices and perform
    any further processing needed for their spectrum representation.

    Attributes:
        info_msg (str): Message printed before and after reading a file.
        optional_columns (list[str]): Columns to include when present, in
            addition to an explicit list of required columns.
    """

    def __init__(self):
        """Set the reading message and start with no optional columns."""
        self.info_msg = 'Reading input file...'
        self.optional_columns = []

    def get_parser(self, extension):
        """Return the reader for an extension without opening a file.

        Args:
            extension (str): Lowercase extension without a dot, such as ``'csv'``
                or ``'xml'``. ECSV uses a separate reader to read its header.

        Returns:
            callable: Bound reader method for the requested format. A recognised
            extension does not guarantee that a subclass implements that reader.

        Raises:
            InvalidExtensionError: The extension is not recognised.
        """
        if extension == 'avro':
            return self._parse_avro
        elif extension == 'csv':
            return self._parse_csv
        elif extension == 'ecsv':
            return self._parse_ecsv
        elif extension == 'fits':
            return self._parse_fits
        elif extension == 'xml':
            return self._parse_xml
        else:
            raise InvalidExtensionError(extension)

    def parse_file(self, file_path: Union[Path, str], disable_info: bool = False):
        """Read a file and standardise recognised column types.

        Args:
            file_path (str or pathlib.Path): Input filename. Gzip-compressed CSV,
                ECSV, FITS and XML files are supported using compound
                extensions such as ``.csv.gz``.
            disable_info (bool): If True, suppress the reading-status messages.
                Defaults to False.

        Returns:
            tuple[pandas.DataFrame, str]: Parsed data and its underlying lowercase
            extension without a dot. For example, ``spectra.csv.gz`` returns
            ``'csv'`` as the extension.

        Raises:
            InvalidExtensionError: The filename does not identify a supported
                format, including when it has no extension.
            FileNotFoundError: The input file does not exist.
            NotImplementedError: The selected reader is not implemented by this
                parser.

        Notes:
            Compressed inputs are read through a binary stream without creating a
            decompressed file. Other errors from file readers or column conversion
            are passed back to the caller.
        """
        if not disable_info:
            self.print_info_msg()
        extension = _get_file_extension(file_path)
        parser = self.get_parser(extension)
        input_context = GenericParser.get_input_context(file_path)
        with input_context as source:
            parsed_data = _cast(parser(source))
        if not disable_info:
            self.print_info_msg(done=True)
        return parsed_data, extension

    @staticmethod
    def get_input_context(file_path: Path | str) -> GzipFile | nullcontext[Path | str]:
        """Create a context manager for a filename or a decompressed input stream.

        Args:
            file_path (str or pathlib.Path): Input filename.

        Returns:
            contextlib.AbstractContextManager: Yields a binary gzip stream when
            the final suffix is ``.gz``, otherwise yields the original filename.
            The gzip stream is closed when the context is exited.

        Notes:
            This helper checks only the final suffix. Format support is determined
            separately by the extension lookup and the selected reader.
        """
        return (gzip.open(file_path, 'rb') if Path(file_path).suffix.lower() == '.gz'
                else nullcontext(file_path))

    def _columns_to_read(self, required_columns, available_columns):
        """Add available optional columns to an explicit column selection.

        Args:
            required_columns (list[str] or None): Requested columns. An empty
                selection or None is returned unchanged, meaning read all columns.
            available_columns (iterable[str]): Column names found in the file.

        Returns:
            list[str] or None: The selection with available optional columns
            appended once. Missing required columns are not removed.

        Notes:
            When ``solution_id`` is optional, its ``solutionId`` alias (for
            internal use) is also retained if present.
        """
        # No column selection means read all columns.
        if not required_columns:
            return required_columns

        columns_to_read = list(required_columns)
        present_optional = get_present_optional_columns(self.optional_columns, available_columns)

        for column in present_optional:
            if column not in columns_to_read:
                columns_to_read.append(column)

        return columns_to_read

    def _parse_avro(self, avro_file):
        """Read Avro data in a subclass that supplies an Avro reader.
        Support for Avro files is intended solely for internal use.
        The Archive does not distribute files in this format.

        Args:
            avro_file (str or pathlib.Path): Input filename.

        Raises:
            NotImplementedError: The base parser has no Avro reader.
        """
        raise NotImplementedError('Method not implemented for base class.')

    def _parse_csv(self, csv_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """Read a CSV table, converting selected array and matrix fields.

        Args:
            csv_file (str, pathlib.Path or file-like): Input filename or readable
                stream supported by the format reader.
            _array_columns (list[str] or None): Columns to convert from stored text or lists to NumPy arrays.
                Defaults to None.
            _matrix_columns (list[tuple[str, str]] or None): Pairs of
                ``(size_column, values_column)`` names. The first column gives each
                matrix dimension; the second holds its packed values and is
                replaced by a symmetric NumPy matrix. Defaults to None.
            _usecols (list[str] or None): Columns to read, with available optional
                columns added. None reads all columns. Defaults to None.

        Returns:
            pandas.DataFrame: Selected table data with the requested conversions.

        Notes:
            Lines starting with ``#`` are skipped. Use ``_parse_ecsv`` to read
            ECSV headers. Scalar floats use pandas' round-trip parsing.
            When optional columns are requested, the stream is moved back to the
            beginning after its header has been read.
        """
        from pandas import read_csv as pd_read_csv

        if _usecols and self.optional_columns:
            available = pd_read_csv(csv_file, comment='#', nrows=0).columns
            if hasattr(csv_file, 'seek'):
                csv_file.seek(0)
            _usecols = self._columns_to_read(_usecols, available)
        df = pd_read_csv(csv_file, comment='#', usecols=_usecols, **CSV_FLOAT_PRECISION_KWARGS)
        return self._convert_array_and_matrix_columns(df, _array_columns, _matrix_columns)

    def _parse_ecsv(self, ecsv_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """Read ECSV data and metadata, preserving floating-point precision.

        Args:
            ecsv_file (str, pathlib.Path or file-like): Filename or seekable
                input stream. Gzip streams are supplied by ``parse_file``.
            _array_columns (list[str] or None): Additional string columns to
                convert to arrays, alongside arrays declared in the header.
            _matrix_columns (list[tuple[str, str]] or None): Size-column and
                packed-value-column pairs to expand into symmetric matrices.
            _usecols (list[str] or None): Columns to retain, including available
                optional columns. None reads all columns.

        Returns:
            pandas.DataFrame: Parsed values with arrays stored in individual
            cells. Header metadata and column attributes are copied into
            ``attrs['ecsv_metadata']``. Declared units are recorded without converting the values.

        Notes:
            Floating-point values are read with float64 precision, including
            values inside arrays. The original data types from the header are
            recorded in ``attrs['ecsv_metadata']``. Integer values remain exact.
            Gaia's ``null`` markers in numeric and array columns are treated as
            missing values. Invalid ECSV files raise an error; the reader does
            not try to read them as CSV.
        """
        from .ecsv_utils import ecsv_to_dataframe, read_ecsv_table

        table, header = read_ecsv_table(ecsv_file, return_header=True)
        columns = self._columns_to_read(_usecols, table.colnames)
        if columns:
            table = table[columns]
        df = ecsv_to_dataframe(table, header)
        return self._convert_array_and_matrix_columns(df, _array_columns, _matrix_columns)

    @staticmethod
    def _convert_array_and_matrix_columns(df, array_columns=None, matrix_columns=None):
        """Convert array cells and expand packed matrices in a parsed table.

        Existing NumPy arrays pass through ``str_to_array`` unchanged. Missing
        array columns are ignored; requested matrix pairs must both be present.
        Return the supplied DataFrame with its converted columns.
        """
        if array_columns:
            for column in array_columns:
                if column in df.columns:
                    df[column] = df[column].apply(str_to_array)
        if matrix_columns:
            for size_column, values_column in matrix_columns:
                df[values_column] = [array_to_symmetric_matrix(str_to_array(array), size)
                                     for array, size in zip(df[values_column], df[size_column])]
        return df

    def _parse_fits(self, fits_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """Read a FITS table and expand selected packed matrix columns.

        Args:
            fits_file (str, pathlib.Path or file-like): Input filename or readable
                stream supported by the format reader.
            _array_columns (list[str] or None): Accepted for compatibility; arrays are read directly by Astropy.
                Defaults to None.
            _matrix_columns (list[tuple[str, str]] or None): Pairs of
                ``(size_column, values_column)`` names. The first column gives each
                matrix dimension; the second holds its packed values and is
                replaced by a symmetric NumPy matrix. Defaults to None.
            _usecols (list[str] or None): Columns to read, with available optional
                columns added. None reads all columns. Defaults to None.

        Returns:
            pandas.DataFrame: Selected table data with the requested conversions.

        Notes:
            Astropy reads the table before column selection. Warnings about the FITS
            unit ``electron`` are suppressed; other warnings are not filtered here.
        """
        import warnings

        from astropy.table import Table
        from astropy.units import UnitsWarning

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UnitsWarning,
                                    message=r".*'electron'.*did not parse as fits unit.*")
            table = Table.read(fits_file, format='fits')

        _usecols = self._columns_to_read(_usecols, table.colnames)
        df = table.to_pandas()[_usecols] if _usecols else table.to_pandas()
        if _matrix_columns:
            for size_column, values_column in _matrix_columns:
                df[values_column] = [array_to_symmetric_matrix(array, size) for array, size in zip(df[values_column],
                                                                                                   df[size_column])]
        return df

    def _parse_xml(self, xml_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """Read an XML/VOTable table and expand selected packed matrix columns.

        Args:
            xml_file (str, pathlib.Path or file-like): Input filename or readable
                stream supported by the format reader.
            _array_columns (list[str] or None): Accepted for compatibility; arrays are read directly by Astropy.
                Defaults to None.
            _matrix_columns (list[tuple[str, str]] or None): Pairs of
                ``(size_column, values_column)`` names. The first column gives each
                matrix dimension; the second holds its packed values and is
                replaced by a symmetric NumPy matrix. Defaults to None.
            _usecols (list[str] or None): Columns to read, with available optional
                columns added. None reads all columns. Defaults to None.

        Returns:
            pandas.DataFrame: Selected table data with the requested conversions.

        Notes:
            The input must contain a single VOTable table. All columns are read first;
            the requested selection is then applied to the resulting DataFrame.
        """
        from astropy.io.votable import parse_single_table

        table = parse_single_table(xml_file).to_table()
        # The columns argument of the parse_single_table function triggers an error in certain versions of Astropy,
        # so all columns are read first, and then the unused ones are removed.
        _usecols = self._columns_to_read(_usecols, table.colnames)
        df = table.to_pandas()[_usecols] if _usecols else table.to_pandas()
        if _matrix_columns:
            for size_column, values_column in _matrix_columns:
                df[values_column] = [array_to_symmetric_matrix(array, size) for array, size in zip(df[values_column],
                                                                                                   df[size_column])]
        return df

    def print_info_msg(self, done=False):
        """Print the reading-status message on the current terminal line.

        Args:
            done (bool): If True, append ``' Done!'`` to the message. Defaults to
                False.
        """
        msg = self.info_msg
        if done:
            msg = msg + ' Done!'
        print(msg, end='\r')


def _get_file_extension(file_path: str | Path):
    """Return the underlying file format, ignoring a supported gzip suffix.

    Args:
        file_path (str or pathlib.Path): Filename to inspect. The file is not
            opened and need not exist.

    Returns:
        str: Lowercase extension without a dot, such as ``'csv'`` for both
        ``spectra.csv`` and ``spectra.csv.gz``. Returns an empty string if no
        extension is found. Unrecognised extensions are returned for the
        caller to validate.
    """
    return get_file_extension(file_path)
