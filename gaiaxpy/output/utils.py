from ast import literal_eval
from os.path import abspath, dirname, join

import numpy as np
import pandas as pd
from astropy.io import fits
from numpy import ndarray


def pandas_from_records(lst):
    return pd.DataFrame.from_records([record.to_dict_func for record in lst])


def _array_to_standard(array, extension='csv'):
    """
    Converts an array to a tuple so that its string representation corresponds to the archive standard where a list is
        represented using parentheses and commas, i.e.: "(elem1, elem2)".

    Args:
        array (ndarray): An array of floats.
        extension (str): Format to use 'csv' means use round brackets, 'ecsv' means use square brackets.

    Returns:
        tuple: The array converted to a tuple.
    """
    if not isinstance(array, ndarray):
        raise ValueError('Input must be a NumPy array.')

    def convert_ecsv(row):
        # Square brackets should be used and nan values should be shown as null (no quotes)
        if np.isnan(np.min(row)):
            return '[' + ', '.join(['null' if np.isnan(value) else str(value) for value in row]) + ']'
        return list(row)

    conversion_functions = {'csv': tuple, 'ecsv': convert_ecsv}
    if array.ndim > 1:
        conversion_function = conversion_functions[extension]
        return conversion_function([conversion_function(row) for row in array])
    else:
        conversion_function = conversion_functions[extension]
        return conversion_function(array)


def _get_array_columns(df):
    return [column for column in df.columns if isinstance(df[column].iloc[0], ndarray)]


def _get_sampling_dict(positions):
    return {'pos': _array_to_standard(positions)}


def _load_header_dict():
    current_path = dirname(abspath(__file__))
    header_dictionary_path = join(current_path, 'ecsv_headers', 'headers_dict.txt')
    with open(header_dictionary_path) as f:
        data = f.read()
    # Load header dictionary
    header_dict = literal_eval(data)
    return header_dict


def _build_ecsv_header(df, positions=None):
    positions = str(list(positions)) if positions is not None else None
    columns = df.columns
    header_dict = _load_header_dict()
    header = _initialise_header()
    data_type = df.attrs['data_type']
    units_dict = data_type.get_units()
    for column in columns:
        header.append('# -')
        header.append(f'#   name: {column}')
        header.append(f'#   datatype: {header_dict[column]["datatype"]}')
        try:
            header.append(
                f'#   subtype: {header_dict[column]["subtype"].replace("null", str(len(df[column].iloc[0])))}')
        except KeyError:
            pass
        header.append(f'#   description: {header_dict[column]["description"]}')
        if units_dict.get(column, None):
            header.append(f'#   unit: {units_dict[column]}')
        if header_dict[column].get('meta', None):
            header.append('#   meta:')
            header.append(f'#     ucd: {header_dict[column]["meta"]}')
    if positions:
        header.append('# meta:')
        header.append(f'#   sampling: {positions}')
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


def _add_ecsv_header(header, output_path, output_file):
    with open(join(output_path, f'{output_file}.ecsv'), "r+") as f:
        s = f.read()
        f.seek(0)
        f.write(header + s)


def _generate_fits_header(_data, _column_formats):
    data_type = _data.attrs['data_type']
    units_dict = data_type.get_units()
    header_dict = _load_header_dict()
    cards = list()
    for index, column in enumerate(_data.columns):
        cards.append((f'TTYPE{index + 1}', column))
        cards.append((f'TFORM{index + 1}', _column_formats.get(column, '')))
        cards.append((f'TCOMM{index + 1}', header_dict.get(column, dict()).get('description', '')))
        cards.append((f'TUCD{index + 1}', header_dict.get(column, dict()).get('meta', '')))
        cards.append((f'TUNIT{index + 1}', units_dict.get(column, '')))
    header = fits.Header(cards=cards)
    return header
