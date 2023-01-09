"""
parse_generic.py
====================================
Module to parse input files containing spectra.
"""

from os.path import splitext

import pandas as pd
from astropy.io.votable import parse_single_table
from astropy.table import Table

from gaiaxpy.core.generic_functions import array_to_symmetric_matrix, str_to_array
from .cast import _cast

valid_extensions = ['avro', 'csv', 'ecsv', 'fits', 'xml']


def _raise_key_error(column):
    raise KeyError(f'The columns in the input data do not match the expected ones. Missing column {column}.')


class DataMismatchError(RuntimeError):
    """
    Error raised when the data in a file is invalid or the file extension does not match the file contents.
    """

    def __init__(self):
        message = 'The file contains invalid data, the data does not match the file extension or the file does not' \
                  ' exist.'
        Exception.__init__(self, message)


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
        elif extension == 'csv' or extension == 'ecsv':
            return self._parse_csv
        elif extension == 'fits':
            return self._parse_fits
        elif extension == 'xml':
            return self._parse_xml
        else:
            raise InvalidExtensionError()

    def parse(self, file_path):
        """
        Parse the input file according to its extension.

        Args:
            file_path (str): Path to a file.

        Returns:
            DataFrame: Pandas DataFrame representing the file.
            str: File extension ('.csv', '.fits', or '.xml').
        """
        extension = _get_file_extension(file_path)
        parser = self.get_parser(extension)
        parsed_data = _cast(parser(file_path))
        return parsed_data, extension

    def _parse_csv(self, csv_file, array_columns=None, matrix_columns=None):
        """
        Parse the input CSV file and store the result in a pandas DataFrame.

        Args:
            csv_file (str): Path to a CSV file.
            array_columns (list): List of columns in the file that contain arrays as strings.
            matrix_columns (list of tuples): List of tuples where the first element is the number of rows/columns of a
                square matrix which values are those contained in the second element of the tuple.

        Returns:
            DataFrame: A pandas DataFrame representing the CSV file.
        """
        converters = {}
        if array_columns is not None:
            converters = dict([(column, lambda x: str_to_array(x)) for column in array_columns])
        try:
            df = pd.read_csv(csv_file, comment='#', float_precision='round_trip', converters=converters)
        except UnicodeDecodeError:
            raise DataMismatchError()
        if matrix_columns is not None:
            for size_column, values_column in matrix_columns:
                df[values_column] = df.apply(lambda row: array_to_symmetric_matrix(str_to_array(row[values_column]),
                                                                                   row[size_column]), axis=1)
        return df

    def _parse_fits(self, fits_file, array_columns=None, matrix_columns=None):
        """
        Parse the input FITS file and store the result in a pandas DataFrame.

        Args:
            fits_file (str): Path to a FITS file.

        Returns:
            DataFrame: A pandas DataFrame representing the FITS file.
        """
        try:
            data = Table.read(fits_file, format='fits')
        except OSError:
            raise DataMismatchError()
        columns = data.columns.keys()
        fits_as_gen = ([data[column][index] for column in columns] for index, _ in enumerate(data))
        df = pd.DataFrame(fits_as_gen, columns=columns)
        if matrix_columns is not None:
            for size_column, values_column in matrix_columns:
                df[values_column] = df.apply(lambda row: array_to_symmetric_matrix(row[values_column],
                                                                                   row[size_column]), axis=1)
        return df

    def _parse_xml(self, xml_file, array_columns=None):
        """
        Parse the input XML file and store the result in a pandas DataFrame.

        Args:
            xml_file (str): Path to an XML file.
            array_columns (list): List of columns in the file that contain arrays as strings.

        Returns:
            DataFrame: A pandas DataFrame representing the XML file.
        """
        try:
            votable = parse_single_table(
                xml_file).to_table(use_names_over_ids=True)
        except ValueError:
            raise DataMismatchError()
        if array_columns:
            columns = list(votable.columns)
            votable_as_list = ([votable[column][index].filled() if column in array_columns else votable[column][index]
                                for column in columns] for index, _ in enumerate(votable))
            return pd.DataFrame(votable_as_list, columns=columns)
        return votable.to_pandas()


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
