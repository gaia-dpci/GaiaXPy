from typing import Union
from pathlib import Path
from gaiaxpy.file_parser.parse_generic import GenericParser


class InverseBasesParser(GenericParser):
    """
    Parser for the inverse bases used in the external calibration.
    """

    def _parse_csv(self, csv_file: Union[Path, str], array_columns: list = None, matrix_columns: list = None):
        """
        Parse the input CSV file and store the result in a pandas DataFrame if it contains inverse bases.

        Args:
            csv_file (Path/str): Path to a CSV file.

        Returns:
            DataFrame: Pandas DataFrame populated with the content of the CSV file.
        """
        return super()._parse_csv(csv_file, array_columns=['inverseBasesCoefficients', 'transformationMatrix'],
                                  matrix_columns=[])
