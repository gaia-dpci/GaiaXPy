"""
parse_internal_continuous.py
====================================
Module to parse input files containing internally calibrated continuous spectra.
"""

import re

import numpy as np
import pandas as pd
from astropy.io.votable import parse_single_table
from fastavro import __version__ as fa_version
from packaging import version

from gaiaxpy.core.generic_functions import array_to_symmetric_matrix
from gaiaxpy.file_parser.parse_generic import DataMismatchError
from .cast import _cast
from .parse_generic import GenericParser
from .utils import _csv_to_avro_map, _get_from_dict

# Columns that contain arrays (as strings)
array_columns = ['bp_coefficients', 'bp_coefficient_errors', 'rp_coefficients', 'rp_coefficient_errors']
# Pairs of the form (matrix_size (N), values_to_put_in_matrix) for columns that contain matrices as strings
matrix_columns = [('bp_n_parameters', 'bp_coefficient_correlations'),
                  ('rp_n_parameters', 'rp_coefficient_correlations')]


class InternalContinuousParser(GenericParser):
    """
    Parser for internally calibrated continuous spectra.
    """

    def _parse_csv(self, csv_file):
        """
        Parse the input CSV file and store the result in a pandas DataFrame if it contains internally calibrated
            continuous spectra.

        Args:
            csv_file (str): Path to a CSV file.

        Returns:
            DataFrame: Pandas DataFrame representing the CSV file.
        """
        return super()._parse_csv(csv_file, array_columns=array_columns, matrix_columns=matrix_columns)

    def _parse_fits(self, fits_file):
        """
        Parse the input FITS file and store the result in a pandas DataFrame if it contains internally calibrated
            continuous spectra.

        Args:
            fits_file (str): Path to a FITS file.

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
        values_to_df = ((value for column, value in zip(columns, entry)) for index, entry in enumerate(votable.array))
        df = pd.DataFrame(values_to_df, columns=columns)
        if matrix_columns is not None:
            for size_column, values_column in matrix_columns:
                try:
                    df[values_column] = df.apply(lambda row:
                                                 array_to_symmetric_matrix(row[values_column], row[size_column]),
                                                 axis=1)
                # Value can be NaN when a band is not present
                except IndexError:
                    continue
        return _cast(df)

    @staticmethod
    def __process_avro_record(record):
        return {key: np.array(_get_from_dict(record, _csv_to_avro_map[key])) if
        isinstance(_get_from_dict(record, _csv_to_avro_map[key]), list) else
        _get_from_dict(record, _csv_to_avro_map[key]) for key in _csv_to_avro_map.keys()}

    @staticmethod
    def __get_records_up_to_1_4_7(avro_file):
        from fastavro import reader
        f = open(avro_file, 'rb')
        avro_reader = reader(f)
        record = avro_reader.next()
        while record:
            try:
                current_record = InternalContinuousParser.__process_avro_record(record)
                yield current_record
            except KeyError:
                raise KeyError("Keys in the input file don't match the expected ones.")
            try:
                record = avro_reader.next()
            except StopIteration:
                f.close()
                break

    @staticmethod
    def __get_records_later_than_1_4_7(avro_file):
        def __yield_records(avro_file):
            from fastavro import block_reader
            with open(avro_file, 'rb') as fo:
                for block in block_reader(fo):
                    for rec in block:
                        yield rec

        records = __yield_records(avro_file)
        for record in records:
            yield InternalContinuousParser.__process_avro_record(record)

    def _parse_avro(self, avro_file):
        """
        Parse the input AVRO file and return the result as a Pandas DataFrame.

        Args:
            avro_file (str): Path to an AVRO file.

        Returns:
            DataFrame: Pandas DataFrame representing the AVRO file.
        """
        if version.parse(fa_version) <= version.parse("1.4.7"):
            __get_records = InternalContinuousParser.__get_records_up_to_1_4_7
        elif version.parse(fa_version) > version.parse("1.4.7"):
            __get_records = InternalContinuousParser.__get_records_later_than_1_4_7
        else:
            raise ValueError(f'Fastavro version {fa_version} may not have been parsed properly.')
        df = pd.DataFrame(__get_records(avro_file))
        # Pairs of the form (matrix_size (N), values_to_put_in_matrix)
        to_matrix_columns = [('bp_n_parameters', 'bp_coefficient_covariances'),
                             ('rp_n_parameters', 'rp_coefficient_covariances')]
        for size_column, values_column in to_matrix_columns:
            try:
                df[values_column] = df.apply(lambda row:
                                             array_to_symmetric_matrix(row[values_column], row[size_column]),
                                             axis=1)
            except TypeError:
                continue  # Value can be NaN when a band is not present
        return _cast(df)
