"""
output_data.py
====================================
Module to represent generic output data.
"""

from gaiaxpy.file_parser.parse_generic import InvalidExtensionError
from .utils import _standardise_output_format


class OutputData(object):

    def __init__(self, data, positions):
        self.data = data.copy()
        self.positions = positions

    def save(self, save_file, output_path, output_file, output_format, extension):
        """
        Save the output data.

        Args:
            save_file (bool): Whether to save the file or not.
            output_path (str): Path where to save the file.
            output_file (str): Name of the output file.
            output_format (str): Format of the output file.
            extension (str): Format of the original input file.
        """
        if save_file:
            if output_file is None:
                raise ValueError('The parameter output_file cannot be None.')
            if output_format is None:
                output_format = extension
            output_format = _standardise_output_format(output_format)
            if output_format == 'avro':
                return self._save_avro(output_path, output_file)
            elif output_format == 'csv':
                return self._save_csv(output_path, output_file)
            elif output_format == 'ecsv':
                return self._save_ecsv(output_path, output_file)
            elif output_format == 'fits':
                return self._save_fits(output_path, output_file)
            elif output_format == 'xml':
                return self._save_xml(output_path, output_file)
            raise InvalidExtensionError()

    def _save_avro(self, output_path, output_file):
        raise NotImplementedError()

    def _save_csv(self, output_path, output_file):
        raise NotImplementedError()

    def _save_ecsv(self, output_path, output_file):
        raise NotImplementedError()

    def _save_fits(self, output_path, output_file):
        raise NotImplementedError()

    def _save_xml(self, output_path, output_file):
        raise NotImplementedError()
