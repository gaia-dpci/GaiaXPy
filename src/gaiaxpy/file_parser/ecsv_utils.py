"""Read ECSV headers and keep array cells when converting to a DataFrame."""
import csv
import sys
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path

import numpy as np
from astropy.io.ascii.ecsv import Ecsv, EcsvHeader


class _Float64EcsvHeader(EcsvHeader):
    """Use float64 precision before converting the stored text."""

    def get_cols(self, lines):
        super().get_cols(lines)
        for column in self.cols:
            for attribute in ('dtype', 'subtype'):
                if getattr(column, attribute) in ('float16', 'float32'):
                    setattr(column, attribute, 'float64')


class _Float64Ecsv(Ecsv):
    """Read ECSV with wider floating-point types and unchanged integer types."""

    header_class = _Float64EcsvHeader


def _read_header(stream):
    """Read the header with Astropy's YAML loader and restore the stream position.

    The full ECSV reader still validates the header against the data.
    """
    from astropy.table.meta import YamlParseError, get_header_from_yaml

    position = stream.tell()
    lines = []
    try:
        for line in stream:
            if isinstance(line, bytes):
                line = line.decode('utf-8')
            if not line.strip():
                continue
            if not line.startswith('#'):
                break
            lines.append((line[2:] if line.startswith('# ') else line[1:]).rstrip('\r\n'))
    finally:
        stream.seek(position)
    # Leave missing or malformed ECSV headers for the format reader to reject.
    if not lines or not lines[0].startswith('%ECSV '):
        return {}
    try:
        header = get_header_from_yaml(lines)
    except YamlParseError as error:
        raise ValueError('Could not read the YAML header in the ECSV file.') from error
    return header if isinstance(header, dict) else {}


def _read_table(source, fill_values):
    """Allow large spectrum cells and restore the CSV reader's field limit."""
    previous_limit = csv.field_size_limit()
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            break
        except OverflowError:
            limit //= 10
    try:
        reader = _Float64Ecsv()
        reader.data.fill_values = fill_values
        return reader.read(source)
    finally:
        csv.field_size_limit(previous_limit)


def read_ecsv_table(source, *, return_header=False):
    """Read an ECSV filename or seekable stream without rounding to float32.

    Floating-point values, including array elements, use float64 precision.
    Integer types and array shapes follow the header. Blank values follow
    Astropy's normal handling; ``null`` also marks missing numeric or array
    cells. Invalid ECSV raises an error rather than being read as CSV.

    Set ``return_header=True`` to return ``(table, header)`` and retain the
    original type declarations alongside the parsed values. Otherwise, return
    only the table. The source file is never modified.
    """
    context = nullcontext(source) if hasattr(source, 'read') else Path(source).open('rb')
    with context as stream:
        position = stream.tell()
        header = _read_header(stream)
        columns = header.get('datatype') or []
        null_columns = [column['name'] for column in columns if isinstance(column, dict) and 'name' in column
                        and (column.get('datatype') not in ('string', 'str')
                             or '[' in (column.get('subtype') or ''))]
        fill_values = [('', '0')]
        if null_columns:
            fill_values.append(('null', '0', *null_columns))
        source = stream.readlines() if isinstance(stream.read(0), str) else stream
        try:
            table = _read_table(source, fill_values)
        except ValueError as error:
            # Astropy's ASCII reader can reject an empty table with fixed-shape
            # arrays. Parse one masked row to establish the shapes, then discard it.
            if 'shape mismatch between value and column specifier' not in str(error):
                raise
            stream.seek(position)
            contents = stream.read()
            if isinstance(contents, bytes):
                contents = contents.decode('utf-8')
            lines = contents.splitlines()
            data_lines = [line for line in lines if line.strip() and not line.startswith('#')]
            if len(data_lines) != 1:
                raise
            empty_row = header.get('delimiter', ' ').join('""' for _ in columns)
            table = _read_table(lines + [empty_row], fill_values)[:0]
        return (table, header) if return_header else table


def _array_value(value):
    """Convert an array cell, preserving missing values before numeric casting."""
    if np.ma.isMaskedArray(value):
        mask = np.ma.getmaskarray(value)
        if np.all(mask):
            return np.nan
        if np.any(mask):
            # Object arrays preserve large integers when some elements are missing.
            dtype = value.dtype if value.dtype.kind in 'fc' else object
            return value.astype(dtype).filled(np.nan)
        return np.asarray(value.data)
    if isinstance(value, (list, tuple, np.ndarray)):
        return np.asarray(value)
    return value


def ecsv_to_dataframe(table, header=None):
    """Keep ECSV arrays in individual DataFrame cells and retain header metadata.

    Masked integers are converted directly to nullable pandas integers to keep
    large identifiers exact. Other scalars use Astropy's pandas conversion.
    Units describe the stored values; this helper does not convert units.
    Table metadata and column attributes are copied into ``attrs['ecsv_metadata']``.
    When supplied, the original header's datatype and subtype declarations
    are preserved in the DataFrame metadata. These describe the input file;
    floating-point values are still read as float64.
    """
    from pandas import DataFrame, NA, array

    array_columns = [name for name in table.colnames
                     if table[name].ndim > 1 or getattr(getattr(table[name], 'dtype', None), 'kind', None) == 'O']
    # Construct masked integers directly: conversion through float64 would round identifiers above 2**53.
    integer_columns = [name for name in table.colnames if name not in array_columns
                       and getattr(getattr(table[name], 'dtype', None), 'kind', None) in ('i', 'u')
                       and np.any(np.ma.getmaskarray(table[name]))]
    scalar_columns = [name for name in table.colnames if name not in array_columns + integer_columns]
    frame = (table[scalar_columns].to_pandas(index=False) if scalar_columns else
             DataFrame(index=range(len(table))))
    for name in integer_columns:
        column = table[name]
        prefix = 'UInt' if column.dtype.kind == 'u' else 'Int'
        values = array(np.asarray(column), dtype=f'{prefix}{column.dtype.itemsize * 8}')
        values[np.ma.getmaskarray(column)] = NA
        frame[name] = values
    for name in array_columns:
        frame[name] = [_array_value(value) for value in table[name]]
    frame = frame[table.colnames]
    attributes = {}
    declarations = {column['name']: column for column in (header or {}).get('datatype', [])}
    for name in table.colnames:
        info = table[name].info
        unit = getattr(info, 'unit', None)
        attributes[name] = {'unit': str(unit) if unit is not None else None,
                            'description': info.description, 'format': info.format,
                            'meta': deepcopy(info.meta)}
        for field in ('datatype', 'subtype'):
            if field in declarations.get(name, {}):
                attributes[name][field] = declarations[name][field]
    frame.attrs['ecsv_metadata'] = {'meta': deepcopy(table.meta), 'columns': attributes}
    return frame
