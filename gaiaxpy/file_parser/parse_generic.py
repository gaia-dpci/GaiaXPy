"""
parse_generic.py
====================================
Module to parse input files containing spectra.
"""
from os.path import splitext

import pandas as pd
from astropy.table import Table

from gaiaxpy.core.generic_functions import array_to_symmetric_matrix, str_to_array
from .cast import _cast

valid_extensions = ['avro', 'csv', 'ecsv', 'fits', 'xml']


def _raise_key_error(column):
    raise KeyError(f'The columns in the input data do not match the expected ones. Missing column {column}.')


class InvalidExtensionError(ValueError):
    """
    Error raised when the extension of the input file is not valid. It inherits from ValueError.
    """

    def __init__(self):
        valid = ', '.join(valid_extensions)
        message = f'Valid extensions are: {valid}.'
        Exception.__init__(self, message)


class GenericParser(object):
    """
    Generic spectra parser.
    """

    def get_parser(self, extension):
        """
        Choose the parser to use based on the extension.

        Args:
            extension (str): File extension including the dot (e.g.: '.csv').

        Returns:
            method: Parse method corresponding to the extension.

        Raises:
            InvalidExtensionError: If the extension is not valid.
        """
        if extension == 'avro':
            return self._parse_avro
        elif extension in ['csv', 'ecsv']:
            return self._parse_csv
        elif extension == 'fits':
            return self._parse_fits
        elif extension == 'xml':
            return self._parse_xml
        else:
            raise InvalidExtensionError()

    def _parse(self, file_path):
        """
        Parse the input file according to its extension.

        Args:
            file_path (str): Path to a file.

        Returns:
            DataFrame: Pandas DataFrame representing the file.
            str: File extension ('.csv', '.fits', or '.xml').
        """
        print('Reading input file...', end='\r')
        extension = _get_file_extension(file_path)
        parser = self.get_parser(extension)
        parsed_data = _cast(parser(file_path))
        return parsed_data, extension

    def _parse_avro(self, avro_file):
        raise NotImplementedError('Method not implemented for base class.')

    def _parse_csv(self, csv_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """
        Parse the input CSV file and store the result in a pandas DataFrame.

        Args:
            csv_file (str): Path to a CSV file.
            _array_columns (list): List of columns in the file that contain arrays as strings.
            _matrix_columns (list of tuples): List of tuples where the first element is the number of rows/columns of a
                square matrix which values are those contained in the second element of the tuple.
            _usecols (list): Columns to read.

        Returns:
            DataFrame: A pandas DataFrame representing the CSV file.
        """
        df = pd.read_csv(csv_file, comment='#', float_precision='high', usecols=_usecols)
        if _array_columns:  # Pandas converters seemed slower
            for column in _array_columns:
                if column in df.columns:
                    df[column] = df[column].apply(lambda x: str_to_array(x))
        if _matrix_columns:
            for size_column, values_column in _matrix_columns:
                df[values_column] = df.apply(lambda row: array_to_symmetric_matrix(str_to_array(row[values_column]),
                                                                                   row[size_column]), axis=1)
        return df

    def _parse_fits(self, fits_file, _array_columns=None, _matrix_columns=None, _usecols=None):
        """
        Parse the input FITS file and store the result in a pandas DataFrame.

        Args:
            fits_file (str): Path to a FITS file.
            _array_columns (list): List of columns in the file that contain arrays as strings.
            _matrix_columns (list of tuples): List of tuples where the first element is the number of rows/columns of a
                square matrix which values are those contained in the second element of the tuple.
            _usecols (list): Columns to read.

        Returns:
            DataFrame: A pandas DataFrame representing the FITS file.
        """
        table = Table.read(fits_file, format='fits')
        df = table.to_pandas()[_usecols] if _usecols else table.to_pandas()
        if _matrix_columns:
            for size_column, values_column in _matrix_columns:
                df[values_column] = df.apply(lambda row: array_to_symmetric_matrix(row[values_column],
                                                                                   row[size_column]), axis=1)
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
        # Astropy won't automatically remove the columns that are not in _usecols but it speeds up the process a bit
        table = Table.read(xml_file, columns=_usecols)
        # Parsing only the required columns would be ideal, but not necessarily issue due to some type issues
        df = table.to_pandas()[_usecols]
        if _matrix_columns:
            for size_column, values_column in _matrix_columns:
                df[values_column] = df.apply(lambda row: array_to_symmetric_matrix(row[values_column],
                                                                                   row[size_column]), axis=1)
        return df


def _get_file_extension(file_path):
    """
    Get the extension of a file.

    Args:
        file_path (str): Path to a file.

    Returns:
        str: File extension (e.g.: '.csv')
    """
    _, file_extension = splitext(file_path)
    return file_extension[1:]
