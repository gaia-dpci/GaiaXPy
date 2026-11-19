"""Save and read the gaiaxpy_metadata attached to output DataFrames.

CSV uses a separate <output_stem>_metadata.csv file. ECSV, FITS and XML/VOTable
embed the metadata in their headers or format metadata. The public
read_output_metadata helper returns the decoded dictionary without loading the
result table. Other DataFrame attrs are not part of this shared metadata
representation.
"""

import csv
import json
from pathlib import Path

from gaiaxpy.core.output_metadata import OUTPUT_METADATA_KEY

CSV_METADATA_PREFIX = f'# {OUTPUT_METADATA_KEY}: '
FITS_METADATA_KEY = 'GXPMETA'
_MISSING = object()
_CSV_METADATA_TYPES = {'string': str, 'integer': int, 'number': float, 'boolean': bool,
                       'null': type(None), 'object': dict, 'array': list}


def encode_output_metadata(data):
    """Encode the DataFrame's GaiaXPy metadata as a JSON string.

    Args:
        data (pandas.DataFrame): Table whose attrs may contain gaiaxpy_metadata.

    Returns:
        str or None: Compact JSON for the metadata dictionary, or None when the
        attribute is absent. Unicode characters are escaped for FITS compatibility.

    Raises:
        ValueError: Metadata is not a dictionary or contains non-finite numbers.
        TypeError: Metadata contains values that cannot be encoded as JSON.

    Notes:
        This serialises only gaiaxpy_metadata and leaves the DataFrame unchanged.
        It checks JSON compatibility, not the meaning of each metadata field.
    """
    if OUTPUT_METADATA_KEY not in data.attrs:
        return None
    metadata = data.attrs[OUTPUT_METADATA_KEY]
    if not isinstance(metadata, dict):
        raise ValueError('Output gaiaxpy_metadata must be a dictionary.')
    return json.dumps(metadata, ensure_ascii=True, allow_nan=False, separators=(',', ':'))


def _decode_metadata(value):
    """Decode a metadata dictionary, accepting JSON text or bytes.

    The internal missing-value becomes an empty dictionary. Other values
    must decode to a dictionary; invalid JSON or another decoded type raises
    ValueError. A dictionary supplied directly is returned without copying.
    """
    if value is _MISSING:
        return {}
    metadata = json.loads(value) if isinstance(value, (str, bytes)) else value
    if not isinstance(metadata, dict):
        raise ValueError('Output gaiaxpy_metadata must be a dictionary.')
    return metadata


def escape_xml_metadata(value):
    """Escape ampersands and angle brackets inside an encoded JSON string.

    JSON Unicode escapes preserve their decoded values while avoiding double
    escaping by some VOTable writers. The input must already be JSON text.
    """
    return value.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')


def _csv_metadata_path(path):
    """Return the Path of <output_stem>_metadata.csv beside the supplied output."""
    path = Path(path)
    return path.with_name(f'{path.stem}_metadata.csv')


def save_csv_metadata(path, metadata_json):
    """Write a CSV metadata companion, or remove a stale companion.

    Args:
        path (str or pathlib.Path): Main output filename. The companion uses the
            same directory and the name <output_stem>_metadata.csv.
        metadata_json (str or None): JSON-encoded metadata dictionary. None
            removes an existing companion without creating a new one.

    Returns:
        None: The companion is written or removed on disk.

    Notes:
        Companions have field, value and type columns. String values are plain
        text; other values use JSON. The type column distinguishes literal
        strings such as '001' and 'null' from numbers and missing values.
        Nested dictionaries and lists remain JSON inside individual CSV cells.
        Existing companions are overwritten. The destination directory must
        already exist; file errors are passed back to the caller.
    """
    metadata_path = _csv_metadata_path(path)
    if metadata_json is None:
        metadata_path.unlink(missing_ok=True)
        return
    metadata = _decode_metadata(metadata_json)
    type_names = {value_type: name for name, value_type in _CSV_METADATA_TYPES.items()}
    rows = []
    for field, value in metadata.items():
        value_type = type_names[type(value)]
        encoded = value if isinstance(value, str) else json.dumps(
            value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
        rows.append((field, encoded, value_type))
    with metadata_path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(('field', 'value', 'type'))
        writer.writerows(rows)


def _read_csv_metadata_file(path):
    # Scientific descriptions can exceed the csv module's default field limit.
    """Decode a typed or legacy CSV metadata companion.

    Args:
        path (pathlib.Path): Existing companion filename.

    Returns:
        dict: Metadata read from field,value,type rows, or from legacy
        field,value rows whose values are all JSON-encoded.

    Raises:
        ValueError: The header, CSV syntax, row layout, JSON value or declared
            type is invalid, or a field name is duplicated.

    Notes:
        String fields retain their literal text. The CSV field-size limit is
        temporarily increased for long descriptions and restored on exit.
    """
    previous_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(max(previous_limit, path.stat().st_size))
        with path.open(encoding='utf-8', newline='') as stream:
            rows = csv.reader(stream, strict=True)
            header = next(rows, None)
            if header not in (['field', 'value', 'type'], ['field', 'value']):
                raise ValueError('Expected CSV metadata columns: field,value,type or legacy field,value.')
            metadata = {}
            for row in rows:
                if len(row) != len(header) or not row[0]:
                    raise ValueError('Each metadata row must contain all the declared columns and a field name.')
                field, value = row[:2]
                if field in metadata:
                    raise ValueError(f'Duplicate metadata field: {field}.')
                if len(header) == 2:
                    # Older companions stored every value, including strings, as JSON.
                    metadata[field] = json.loads(value)
                    continue
                value_type = row[2]
                if value_type not in _CSV_METADATA_TYPES:
                    raise ValueError(f'Unknown metadata type {value_type!r} for field {field!r}.')
                decoded = value if value_type == 'string' else json.loads(value)
                if type(decoded) is not _CSV_METADATA_TYPES[value_type]:
                    raise ValueError(f'Metadata value for field {field!r} does not match type {value_type!r}.')
                metadata[field] = decoded
            return metadata
    except (ValueError, csv.Error) as error:
        raise ValueError(f'Invalid CSV metadata in {path}: {error}') from error
    finally:
        csv.field_size_limit(previous_limit)


def _read_csv_metadata(path):
    """Find CSV metadata in a companion, or in legacy leading comments.

    A filename stem ending in _metadata, ignoring case, is read directly as a
    companion. Otherwise, an existing companion takes precedence over embedded
    comments. Missing metadata returns an empty dictionary; malformed or
    duplicate metadata raises an error.
    """
    if path.stem.lower().endswith('_metadata'):
        return _read_csv_metadata_file(path)
    metadata_path = _csv_metadata_path(path)
    if metadata_path.exists():
        return _read_csv_metadata_file(metadata_path)
    # Retain support for older outputs with embedded comment metadata.
    value = _MISSING
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            if not line.startswith('#'):
                break
            if line.startswith(CSV_METADATA_PREFIX):
                if value is not _MISSING:
                    raise ValueError('Duplicate output metadata headers.')
                value = line[len(CSV_METADATA_PREFIX):]
    return value


def _read_ecsv_metadata(path):
    """Read GaiaXPy metadata from the leading ECSV YAML header.

    Accept ordinary and YAML ordered mappings for table metadata. Return the
    stored value or an empty dictionary if no metadata is available. Invalid
    mapping types raise ValueError; YAML parsing errors are passed back to
    the caller.
    """
    import yaml

    comments = []
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            if not line.startswith('#'):
                break
            comments.append(line[2:] if line.startswith('# ') else line[1:])

    header = yaml.safe_load(''.join(comments)) or {}
    if not isinstance(header, dict):
        raise ValueError('Expected an ECSV metadata mapping.')

    meta = header.get('meta')
    if meta is None:
        meta = {}
    # Astropy serialises table metadata as a YAML ordered mapping (!!omap).
    if isinstance(meta, list) and meta and all(isinstance(item, tuple) and len(item) == 2 for item in meta):
        meta = dict(meta)
    if not isinstance(meta, dict):
        raise ValueError('Expected an ECSV metadata mapping.')

    return meta.get(OUTPUT_METADATA_KEY, _MISSING)


def _read_fits_metadata(path):
    """Read GXPMETA from the primary FITS header, without reading table data.

    Return the stored value or an empty dictionary if no metadata is present.
    """
    from astropy.io import fits

    return fits.getheader(path, 0).get(FITS_METADATA_KEY, _MISSING)


def _read_xml_metadata(path):
    """Read the GaiaXPy PARAM value before the VOTable DATA element.

    Return the stored value or an empty dictionary if no metadata is present.
    Duplicate metadata parameters raise ValueError. Table rows and binary
    payloads are not parsed.
    """
    from xml.etree import ElementTree

    value = _MISSING
    # Stop at DATA so large TABLEDATA/BINARY payloads are not parsed.
    with path.open('rb') as stream:
        for event, node in ElementTree.iterparse(stream, events=('start', 'end')):
            tag = node.tag.rsplit('}', 1)[-1]
            if event == 'start' and tag == 'DATA':
                break
            if event == 'end':
                if tag == 'PARAM' and node.get('name') == OUTPUT_METADATA_KEY:
                    if value is not _MISSING:
                        raise ValueError('Duplicate output metadata parameters.')
                    value = node.get('value')
                node.clear()
    return value


def _read_avro_metadata(path):
    """Read the GaiaXPy value from an Avro container header.

    Return the stored value or an empty dictionary without
    iterating over the records.
    """
    from fastavro import reader

    with path.open('rb') as stream:
        return reader(stream).metadata.get(OUTPUT_METADATA_KEY, _MISSING)


def read_output_metadata(file_path):
    """Read GaiaXPy metadata from a saved output without loading its data table.

    Args:
        file_path (str or pathlib.Path): Existing CSV, ECSV, FITS, XML/VOTable,
            or Avro filename. For CSV, either the main output or its
            <output_stem>_metadata.csv companion may be supplied. Avro support
            is intended for internal use only. The Archive does not distribute
            Avro files.

    Returns:
        dict: Decoded gaiaxpy_metadata, or an empty dictionary when absent.
        Each call reads a new dictionary, including its nested values. This
        contains GaiaXPy metadata, not every header field or the sampling grid.

    Raises:
        FileNotFoundError: file_path does not identify an existing file.
        ValueError: The extension is unsupported, the decoded metadata is not
            a dictionary, or the metadata has an invalid value or structure.

    Notes:
        For a main CSV file, the companion is found automatically. A companion
        can also be read directly without the main file. Keep the two together
        when moving a complete CSV output. A CSV stem ending in _metadata is
        interpreted as a companion, ignoring case.

        Current companions use field,value,type columns. Older field,value
        companions with JSON-encoded values are supported, as are older CSV
        outputs with metadata in leading comments when no companion exists.

        This helper decodes metadata; it does not restore it to a DataFrame,
        validate configuration versions, or apply corrections. Other file and
        format-reader errors are passed back to the caller.

    Examples:
        >>> from gaiaxpy.output import read_output_metadata
        >>> metadata = read_output_metadata('output_spectra.csv')  # doctest: +SKIP
        >>> metadata = read_output_metadata('output_spectra_metadata.csv')  # doctest: +SKIP
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f'Output file not found: {path}')

    readers = {
        '.csv': _read_csv_metadata,
        '.ecsv': _read_ecsv_metadata,
        '.fits': _read_fits_metadata,
        '.xml': _read_xml_metadata,
        '.avro': _read_avro_metadata
    }
    suffix = path.suffix.lower()
    try:
        read_metadata = readers[suffix]
    except KeyError:
        raise ValueError(f'Unsupported output metadata format: {suffix}') from None

    return _decode_metadata(read_metadata(path))
