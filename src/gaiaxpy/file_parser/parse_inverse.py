"""Read inverse-basis tables used for external calibration."""

from pathlib import Path
from typing import Union

from gaiaxpy.file_parser.parse_generic import GenericParser


class InverseBasesParser(GenericParser):
    """Read inverse-basis configuration tables using the shared format readers.

    The CSV and ECSV readers convert ``inverseBasesCoefficients`` and
    ``transformationMatrix`` by default.
    """

    def _parse_ecsv(self, ecsv_file, _array_columns=None, _matrix_columns=None):
        """Read ECSV inverse bases, retaining header metadata and array shapes.

        Arguments and conversion defaults follow ``_parse_csv``. Return a
        DataFrame with the requested array and packed-matrix conversions.
        """
        if _array_columns is None:
            _array_columns = ['inverseBasesCoefficients', 'transformationMatrix']
        return super()._parse_ecsv(ecsv_file, _array_columns=_array_columns,
                                   _matrix_columns=_matrix_columns)

    def _parse_csv(self, csv_file: Union[Path, str], _array_columns=None, _matrix_columns=None):
        """Read a CSV inverse-basis table and convert its array fields.

        Args:
            csv_file (str, pathlib.Path or file-like): Input filename or readable
                CSV stream.
            _array_columns (list[str] or None): Columns to convert to NumPy arrays.
                None uses ``inverseBasesCoefficients`` and ``transformationMatrix``;
                an empty list disables those conversions.
            _matrix_columns (list[tuple[str, str]] or None): Pairs of size-column
                and packed-value-column names for matrix expansion. No matrix
                columns are expanded by default.

        Returns:
            pandas.DataFrame: Table data with the requested array and matrix
            conversions.
        """
        if _matrix_columns is None:
            _matrix_columns = []
        if _array_columns is None:
            _array_columns = ['inverseBasesCoefficients', 'transformationMatrix']
        return super()._parse_csv(csv_file, _array_columns=_array_columns, _matrix_columns=_matrix_columns)
