"""
parse_external.py
====================================
Module to parse input files containing externally calibrated sampled spectra.
"""

from .parse_generic import *

# Columns that contain arrays (as strings)
array_columns = ['wl', 'flux', 'flux_error']


class ExternalParser(GenericParser):
    """
    Parser for externally calibrated sampled spectra.
    """

    def _parse_csv(self, csv_file, array_columns=array_columns):
        """
        Parse the input CSV file and store the result in a pandas DataFrame if it
        contains externally calibrated sampled spectra.

        Args:
            csv_file (str): Path to a CSV file.
            array_columns (list): List of columns in the file that contain arrays as strings.

        Returns:
            DataFrame: Pandas DataFrame representing the CSV file.
        """
        return super()._parse_csv(csv_file, array_columns)

    def _parse_fits(self, fits_file, array_columns=array_columns):
        """
        Parse the input FITS file and store the result in a pandas DataFrame if it
        contains externally calibrated sampled spectra.

        Args:
            fits_file (str): Path to an FITS file.
            array_columns (list): List of columns in the file that contain arrays as strings.

        Returns:
            DataFrame: Pandas DataFrame representing the FITS file.
        """
        return super()._parse_fits(fits_file, array_columns=array_columns)

    def _parse_xml(self, xml_file, array_columns=array_columns):
        """
        Parse the input XML file and store the result in a pandas DataFrame if it
        contains externally calibrated sampled spectra.

        Args:
            xml_file (str): Path to an XML file.
            array_columns (list): List of columns in the file that contain arrays as strings.

        Returns:
            DataFrame: Pandas DataFrame representing the XML file.
        """
        return super()._parse_xml(xml_file, array_columns=array_columns)
