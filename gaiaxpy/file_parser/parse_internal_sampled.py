"""
parse_internal_sampled.py
====================================
Module to parse input files containing internally calibrated sampled spectra.
"""

from .parse_generic import GenericParser
from ..core.generic_functions import _warning


class InternalSampledParser(GenericParser):
    """
    Parser for internally calibrated sampled spectra.
    """

    def _parse_csv(self, csv_file, additional_columns=None):
        """
        Parse the input CSV file and store the result in a pandas DataFrame if it contains internally calibrated sampled
            spectra.

        Args:
            csv_file (str): Path to a CSV file.
            additional_columns (dict/list): Parameter required in the parser hierarchy. Not used in this function.

        Returns:
            DataFrame: Pandas DataFrame representing the CSV file.
        """
        if additional_columns:
            _warning(f'Parameter additional_columns not implemented. It will be ignored.')
        return super()._parse_csv(csv_file, _array_columns=['flux', 'error'])
