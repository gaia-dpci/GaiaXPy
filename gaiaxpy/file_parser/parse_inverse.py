from pathlib import Path
from typing import Union

from gaiaxpy.core.generic_functions import _warning
from gaiaxpy.file_parser.parse_generic import GenericParser


class InverseBasesParser(GenericParser):
    """
    Parser for the inverse bases used in the external calibration.
    """

    def _parse_csv(self, csv_file: Union[Path, str], _array_columns=None, _matrix_columns=None, additional_columns=None):
        """
        Parse the input CSV file and store the result in a pandas DataFrame if it contains inverse bases.

        Args:
            csv_file (Path/str): Path to a CSV file.
            additional_columns (dict/list): Parameter required in the parser hierarchy. Not used in this function.

        Returns:
            DataFrame: Pandas DataFrame populated with the content of the CSV file.
        """
        if additional_columns:
            _warning(f'Parameter additional_columns not implemented. It will be ignored.')
        if _matrix_columns is None:
            _matrix_columns = []
        if _array_columns is None:
            _array_columns = ['inverseBasesCoefficients', 'transformationMatrix']
        return super()._parse_csv(csv_file, _array_columns=_array_columns, _matrix_columns=_matrix_columns)
