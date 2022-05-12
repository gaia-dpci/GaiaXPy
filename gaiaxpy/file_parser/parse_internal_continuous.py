"""
parse_internal_continuous.py
====================================
Module to parse input files containing internally calibrated continuous spectra.
"""

import numpy as np
import pandas as pd
import re
from fastavro import reader
from astropy.io.votable import parse_single_table
from .parse_generic import GenericParser
from .utils import _csv_to_avro_map, _get_from_dict
from gaiaxpy.core import array_to_symmetric_matrix
from gaiaxpy.file_parser import DataMismatchError
from .cast import _cast

# Avoid warning, false positive
pd.options.mode.chained_assignment = None

# Columns that contain arrays (as strings)
array_columns = [
    'bp_coefficients',
    'bp_coefficient_errors',
    'rp_coefficients',
    'rp_coefficient_errors']
# Pairs of the form (matrix_size (N), values_to_put_in_matrix) for columns
# that contain matrices as strings
matrix_columns = [('bp_n_parameters', 'bp_coefficient_correlations'),
                  ('rp_n_parameters', 'rp_coefficient_correlations')]


class InternalContinuousParser(GenericParser):
    """
    Parser for internally calibrated continuous spectra.
    """

    def _parse_csv(self, csv_file):
        """
        Parse the input CSV file and store the result in a pandas DataFrame if it
        contains internally calibrated continuous spectra.

        Args:
            csv_file (str): Path to a CSV file.

        Returns:
            DataFrame: Pandas DataFrame representing the CSV file.
        """
        return super()._parse_csv(
            csv_file,
            array_columns=array_columns,
            matrix_columns=matrix_columns)

    def _parse_fits(self, fits_file):
        """
        Parse the input FITS file and store the result in a pandas DataFrame if it
        contains internally calibrated continuous spectra.

        Args:
            csv_file (str): Path to a FITS file.

        Returns:
            DataFrame: Pandas DataFrame representing the FITS file.
        """
        return super()._parse_fits(
            fits_file,
            array_columns=array_columns,
            matrix_columns=matrix_columns)

    def _parse_xml(self, xml_file):
        """
        Parse the input XML file and store the result in a pandas DataFrame.

        Args:
            xml_file (str): Path to an XML file.
            array_columns (list): List of columns in the file that contain arrays as strings.

        Returns:
            DataFrame: A pandas DataFrame representing the XML file.
        """
        try:
            votable = parse_single_table(xml_file)
        except ValueError:
            raise DataMismatchError()
        columns = [re.search('<FIELD ID="(.+?)"', str(field)).group(1) for field in votable.fields]
        values_to_df = []
        for index, entry in enumerate(votable.array):
            row = []
            for column, value in zip(columns, entry):
                row.append(value)
            values_to_df.append(row)
        df = pd.DataFrame(values_to_df, columns=columns)
        if matrix_columns is not None:
            for index, row in df.iterrows():
                for size_column, values_column in matrix_columns:
                    try:
                        df[values_column][index] = array_to_symmetric_matrix(
                            df[size_column][index].astype(int), row[values_column])
                    # Value can be NaN when a band is not present
                    except IndexError:
                        continue
        return _cast(df)

    def _parse_avro(self, avro_file):
        """
        Parse the input AVRO file and return the result as a Pandas DataFrame.

        Args:
            avro_file (str): Path to an AVRO file.

        Returns:
            DataFrame: Pandas DataFrame representing the AVRO file.
        """
        def _avro_file_to_df(avro_file):
            records_list = []
            f = open(avro_file, 'rb')
            avro_reader = reader(f)
            record = avro_reader.next()
            while record:
                try:
                    current_record = {}
                    for key in _csv_to_avro_map.keys():
                        # Access the record and get the value corresponding to the key
                        # If the record is a list, it must be converted to numpy array
                        value = _get_from_dict(record, _csv_to_avro_map[key])
                        if isinstance(value, list):
                            value = np.array(value)
                        # Add this value to a dictionary which represents the current
                        # record
                        current_record[key] = value
                    # Append this record to the global list
                    records_list.append(current_record)
                except KeyError:
                    raise KeyError("Keys in the input file don't match the expected ones.")
                try:
                    # Move onto the next record
                    record = avro_reader.next()
                except StopIteration:
                    # Reached end on file, close it and break
                    f.close()
                    break
            # Records to DataFrame
            return pd.DataFrame(records_list)
        # Pairs of the form (matrix_size (N), values_to_put_in_matrix) for columns
        # that contain matrices as strings
        to_matrix_columns = [('bp_n_parameters', 'bp_coefficient_covariances'),
                             ('rp_n_parameters', 'rp_coefficient_covariances')]
        df = _avro_file_to_df(avro_file)
        for index, row in df.iterrows():
            for size_column, values_column in to_matrix_columns:
                try:
                    df[values_column][index] = array_to_symmetric_matrix(
                        df[size_column][index].astype(int), row[values_column])
                # Value can be NaN when a band is not present
                except TypeError:
                    continue
        return _cast(df)
