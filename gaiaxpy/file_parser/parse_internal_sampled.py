"""
parse_internal_sampled.py
====================================
Module to parse input files containing internally calibrated sampled spectra.
"""

from .parse_generic import GenericParser


class InternalSampledParser(GenericParser):
    """
    Parser for internally calibrated sampled spectra.
    """

    def _parse_csv(self, csv_file):
        """
        Parse the input CSV file and store the result in a pandas DataFrame if it
        contains internally calibrated sampled spectra.

        Args:
            csv_file (str): Path to a CSV file.

        Returns:
            DataFrame: Pandas DataFrame representing the CSV file.
        """
        return super()._parse_csv(
            csv_file,
            array_columns=[
                'flux',
                'error'])
