"""
parse_generic.py
====================================
Module to parse input files containing spectra.
"""

import os
import numpy as np
import pandas as pd
from astropy.table import Table
from astropy.io.votable import parse_single_table
from .cast import _cast
from gaiaxpy.core import array_to_symmetric_matrix

# Avoid warning, false positive
pd.options.mode.chained_assignment = None

valid_extensions = ['avro', 'csv', 'ecsv', 'fits', 'xml']


def _raise_key_error(column):
    raise KeyError(f'The columns in the input data do not match the expected ones. Missing column {column}.')


class DataMismatchError(RuntimeError):
    """
    Error raised when the data in a file is invalid or the file extension does not match the file contents.
    """

    def __init__(self):
        message = 'The file contains invalid data or the data does not match the file extension.'
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
            matrix_columns (list of tuples): List of tuples where the first element is the number
            of rows/columns of a square matrix which values are those contained in the second
            element of the tuple.

        Returns:
            DataFrame: A pandas DataFrame representing the CSV file.
        """
        converters = None
        if array_columns is not None:
            converters = dict([(column, lambda x: np.fromstring(x[1:-1], sep=',')) for column in array_columns])
        try:
            df = pd.read_csv(csv_file, comment='#', float_precision='round_trip', converters=converters)
        except UnicodeDecodeError:
            raise DataMismatchError()
        if matrix_columns is not None:
            for index, row in df.iterrows():
                for size_column, values_column in matrix_columns:
                    try:
                        df[values_column][index] = array_to_symmetric_matrix(
                            df[size_column][index].astype(int), np.fromstring(row[values_column][1:-1], sep=','))
                    # Value can be NaN when a band is not present
                    except TypeError:
                        continue
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
        fits_as_list = []
        columns = data.columns.keys()
        for index, row in enumerate(data):
            # Append row values to list
            row = []
            for column in columns:
                row.append(data[column][index])
            fits_as_list.append(row)
        df = pd.DataFrame(fits_as_list, columns=columns)
        if array_columns is not None:
            for column in array_columns:
                for index, row in df.iterrows():
                    try:
                        df[column][index] = row[column]
                    # Value can be NaN when a band is not present
                    except TypeError:
                        continue
        if matrix_columns is not None:
            for index, row in df.iterrows():
                for size_column, values_column in matrix_columns:
                    try:
                        df[values_column][index] = array_to_symmetric_matrix(
                            df[size_column][index].astype(int), row[values_column])
                    # Value can be NaN when a band is not present
                    except IndexError:
                        continue
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
            votable_as_list = []
            for index, row in enumerate(votable):
                # Append row values to list
                row = []
                for column in columns[:-len(array_columns)]:
                    row.append(votable[column][index])
                # Remove mask
                for column in array_columns:
                    try:
                        row.append(votable[column][index].filled())
                    except KeyError:
                        raise KeyError(f'The columns in the input data do not match the expected ones. Missing column {column}.')
                votable_as_list.append(row)
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
    filename, file_extension = os.path.splitext(file_path)
    return file_extension[1:]
