"""
output_data.py
====================================
Module to represent generic output data.
"""
from ast import literal_eval
from os.path import dirname, abspath, join

from gaiaxpy.core.generic_functions import standardise_extension
from gaiaxpy.file_parser.parse_generic import InvalidExtensionError


def _load_header_dict():
    current_path = dirname(abspath(__file__))
    header_dictionary_path = join(current_path, 'ecsv_headers', 'headers_dict.txt')
    with open(header_dictionary_path) as f:
        data = f.read()
    # Load header dictionary
    header_dict = literal_eval(data)
    return header_dict


def _build_regular_header(columns):
    header_dict = _load_header_dict()
    header = _initialise_header()
    for column in columns:
        header.append('# -')
        header.append(f'#   name: {column}')
        header.append(f'#   datatype: {header_dict[column]["datatype"]}')
        try:
            header.append(f'#   subtype: {header_dict[column]["subtype"]}')
        except KeyError:
            pass
        header.append(f'#   description: {header_dict[column]["description"]}')
    return '\n'.join(header) + '\n'


def _initialise_header():
    return ["# %ECSV 1.0", "# ---", "# delimiter: ','", "# datatype:"]


def _build_photometry_header(columns):
    header_dict = _load_header_dict()
    header = _initialise_header()
    for column in columns:
        header.append('# -')
        header.append(f'#   name: {column}')
        if column != 'source_id':
            if '_flux_error_' in column:
                parameter = '_flux_error_'
            elif '_flux_' in column:
                parameter = '_flux_'
            elif '_mag_' in column:
                parameter = '_mag_'
            system, band = column.split(parameter)
            parameter = f'phot{parameter}'[:-1]
            header.append(f'#   datatype: {header_dict[parameter]["datatype"]}')
            header.append(f'#   description: {header_dict[parameter]["description"]} {band} band')
        else:
            header.append(f'#   datatype: {header_dict[column]["datatype"]}')
            header.append(f'#   description: {header_dict[column]["description"]}')
    return '\n'.join(header) + '\n'


def _add_header(header, output_path, output_file):
    with open(join(output_path, f'{output_file}.ecsv'), "r+") as f:
        s = f.read()
        f.seek(0)
        f.write(header + s)


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
            print('Saving file...', end='\r')
            output_format = standardise_extension(output_format)
            if output_format == 'avro':
                self._save_avro(output_path, output_file)
            elif output_format == 'csv':
                self._save_csv(output_path, output_file)
            elif output_format == 'ecsv':
                self._save_ecsv(output_path, output_file)
            elif output_format == 'fits':
                self._save_fits(output_path, output_file)
            elif output_format == 'xml':
                self._save_xml(output_path, output_file)
            else:
                raise InvalidExtensionError()
            print(f"Done! Output saved to path: {join(output_path, output_file + '.' + output_format)}", end='\r')

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
