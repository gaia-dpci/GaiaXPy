"""Build output filenames, array representations and ECSV/FITS column headers."""

import re
from ast import literal_eval
from os.path import abspath, dirname, join
from pathlib import Path

import numpy as np
from astropy.io import fits
from numpy import ndarray


def _prepare_output_path(output_path, output_file, extension):
    """Create the destination directory and return the output filename.

    Args:
        output_path (str or pathlib.Path): Destination directory.
        output_file (str): Filename stem.
        extension (str): Format extension without a dot.

    Returns:
        pathlib.Path: <output_path>/<output_file>.<extension>. No data file is
        opened here; existing files are not checked or removed.
    """
    Path(output_path).mkdir(parents=True, exist_ok=True)
    return Path(output_path) / f'{output_file}.{extension}'


def _array_to_standard(array, extension='csv'):
    """Prepare numeric arrays for CSV or ECSV cell serialisation.

    Args:
        array (list, numpy.ndarray or None): One- or two-dimensional numeric
            array. None is passed through unchanged.
        extension (str): 'csv' produces tuples with round brackets; 'ecsv'
            produces lists with square brackets and uses null for NaN values.

    Returns:
        tuple, list, str or None: Tuples for CSV; lists for ECSV without NaN,
        or bracketed text when a row contains NaN. Two-dimensional arrays are
        converted row by row and then as a collection of rows.

    Raises:
        ValueError: The input is neither a list, a NumPy array nor None, or an
            ECSV row is empty and its minimum cannot be calculated.
        KeyError: extension is neither 'csv' nor 'ecsv'.

    Notes:
        The return value is not always text; the table writer supplies the final
        cell representation. NaN-to-null conversion is intended for one-dimensional
        ECSV cells; matrices containing NaN need separate handling. This helper
        does not change numeric precision.
    """
    if array is None:
        return array
    if not isinstance(array, (list, ndarray)):
        raise ValueError(f'Input must be a NumPy array or a list, but was {type(array).__name__}.')

    def convert_ecsv(row):
        # Square brackets should be used and nan values should be shown as null (no quotes)
        """Convert a numeric row to a list, using bracketed null text if it contains NaN."""
        if np.isnan(np.min(row)):
            return '[' + ', '.join(['null' if np.isnan(value) else str(value) for value in row]) + ']'
        return list(row)

    conversion_functions = {'csv': tuple, 'ecsv': convert_ecsv}
    array = np.asarray(array)
    if array.ndim > 1:
        conversion_function = conversion_functions[extension]
        return conversion_function([conversion_function(row) for row in array])
    else:
        conversion_function = conversion_functions[extension]
        return conversion_function(array)


def _get_sampling_dict(positions):
    """Return the sampling positions as a pos field using CSV-style tuples."""
    return {'pos': _array_to_standard(positions)}


def _load_header_dict():
    """Read and return the bundled column descriptions and ECSV type declarations."""
    current_path = dirname(abspath(__file__))
    header_dictionary_path = join(current_path, 'ecsv_headers', 'headers_dict.txt')
    with open(header_dictionary_path) as f:
        data = f.read()
    # Load header dictionary
    header_dict = literal_eval(data)
    return header_dict


def _get_col_subtype_len(_df, _column):
    """Return the length of the first cell that supports len().

    Args:
        _df (pandas.DataFrame): Table containing the array column.
        _column (str): Column name to inspect.

    Returns:
        int: Length of the first cell with a defined length. Scalars are
        skipped; an empty array returns zero.

    Raises:
        ValueError: The table is empty or no cell supports len().
        KeyError: The requested column is absent.
    """
    for index in range(0, len(_df)):
        try:
            return len(_df[_column].iloc[index])
        except TypeError:
            pass
    raise ValueError('All arrays in the data seem to be empty. This should never happen.')


def _build_ecsv_header(df, positions=None):
    """Build an ECSV header for spectrum columns and optional sampling.

    Args:
        df (pandas.DataFrame): Result with recognised header-dictionary columns.
            Its data_type attr must provide get_units(). Array subtype lengths
            are inferred from the supplied column cells.
        positions (array-like or None): Common sampling grid to include in table
            metadata.

    Returns:
        str: Comment-prefixed ECSV header ending with a newline. GaiaXPy output
        metadata is added separately by the writer.

    Raises:
        KeyError: data_type or a column definition is missing.
        ValueError: A required array length cannot be obtained.
    """
    positions = None if positions is None else str(list(positions))
    columns = df.columns
    header_dict = _load_header_dict()
    header = _initialise_header()
    data_type = df.attrs['data_type']
    units_dict = data_type.get_units()
    for column in columns:
        current_column = header_dict[column]
        header.append('# -')
        header.append(f'#   name: {column}')
        header.append(f'#   datatype: {current_column["datatype"]}')
        if 'subtype' in current_column.keys():
            header.append(
                f'#   subtype: {current_column["subtype"].replace("null", str(_get_col_subtype_len(df, column)))}')
        header.append(f'#   description: {current_column["description"]}')
        if units_dict.get(column, None):
            header.append(f'#   unit: {units_dict[column]}')
        if current_column.get('meta', None):
            header.append('#   meta:')
            header.append(f'#     ucd: {current_column["meta"]}')
    if positions:
        header.append('# meta:')
        header.append(f'#   sampling: {positions}')
    return '\n'.join(header) + '\n'


def _initialise_header():
    """Return the opening lines of a comma-delimited ECSV 1.0 header."""
    return ["# %ECSV 1.0", "# ---", "# delimiter: ','", "# datatype:"]


def _build_photometry_header(columns):
    """Build ECSV column declarations for synthetic photometry.

    Args:
        columns (iterable[str]): source_id and photometry names with a system
            label, quantity separator and passband. Supported quantities are
            mag, flux, flux_error and within_range. System labels may include
            additional-system versions.

    Returns:
        str: Comment-prefixed ECSV header with column types and descriptions.
        Names are preserved; quantity and passband are extracted for descriptions.

    Raises:
        ValueError: A column other than source_id has no recognised photometry
            quantity separator.
    """
    header_dict = _load_header_dict()
    header = _initialise_header()
    for column in columns:
        header.append('# -')
        header.append(f'#   name: {column}')
        if column == 'source_id':
            header.append(f'#   datatype: {header_dict[column]["datatype"]}')
            header.append(f'#   description: {header_dict[column]["description"]}')
            continue
        # Match the final quantity separator, allowing quantity words inside system/version labels.
        match = re.fullmatch(r'(.+)_(flux_error|flux|mag|within_range)_(.+)', column)
        if match is None:
            raise ValueError(f'Unrecognised photometry column: {column}')
        _, quantity, band = match.groups()
        if quantity == 'within_range':
            header.append('#   datatype: bool')
            header.append(f'#   description: Within the standardisation validity range for the {band} band.')
        else:
            parameter = f'phot_{quantity}'
            header.append(f'#   datatype: {header_dict[parameter]["datatype"]}')
            header.append(f'#   description: {header_dict[parameter]["description"]} {band} band')
    return '\n'.join(header) + '\n'


def _add_ecsv_header(header, filepath):
    """Prepend an ECSV header to an existing text table in place.

    Args:
        header (str): Complete header text, including its final newline.
        filepath (str or pathlib.Path): Existing writable table file.

    Notes:
        The existing file contents are read into memory, then rewritten after
        the header. File errors are passed back to the caller.
    """
    with open(filepath, 'r+') as f:
        s = f.read()
        f.seek(0)
        f.write(header + s)


def _generate_fits_header(_data, _column_formats):
    """Build FITS column-name, format, description, UCD and unit cards.

    Args:
        _data (pandas.DataFrame): Result whose data_type attr provides get_units().
        _column_formats (dict): Column names mapped to FITS format strings.

    Returns:
        astropy.io.fits.Header: Column cards in DataFrame column order. Missing
        descriptions, formats, UCDs and units use empty strings.
    """
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
