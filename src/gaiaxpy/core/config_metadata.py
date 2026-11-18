"""
Embedded metadata for configuration files.

This module reads file metadata only.
"""
import json
from pathlib import Path

import numpy as np
import yaml

from gaiaxpy.core.generic_variables import RELEASES, YAML_EXTENSIONS, INV_BASIS_TYPES

NPZ_METADATA_KEY = '__gaiaxpy_metadata__'
METADATA_KEY = 'gaiaxpy_metadata'
CSV_METADATA_PREFIX = '# gaiaxpy_metadata: '


def validate_config_metadata(metadata, *, additional_filter=False):
    """
    Validate metadata without guessing missing information.

    By default, require the complete packaged-configuration schema. Additional
    filters require only a version, validating other known fields when supplied.
    """
    if not isinstance(metadata, dict):
        raise ValueError('Metadata must be a dictionary.')
    if not additional_filter or 'schema_version' in metadata:
        if type(metadata.get('schema_version')) is not int or metadata['schema_version'] != 1:
            raise ValueError('Expected metadata schema_version=1.')
    required_fields = (('version',) if additional_filter else
                       ('version', 'component_type', 'data_release', 'original_filename', 'description'))
    for field in ('version', 'component_type', 'data_release', 'original_filename', 'description', 'reference'):
        if field in required_fields or field in metadata:
            if not isinstance(metadata.get(field), str) or not metadata[field].strip():
                raise ValueError(f'Metadata field {field!r} must be a non-empty string.')
    if 'data_release' in metadata and metadata['data_release'] not in RELEASES:
        raise ValueError(f'Metadata data_release must be one of: {", ".join(RELEASES)}.')
    if 'original_filename' in metadata and Path(metadata['original_filename']).name != metadata['original_filename']:
        raise ValueError('original_filename must be a filename, not a path.')
    if not additional_filter or 'changes' in metadata:
        changes = metadata.get('changes')
        if not isinstance(changes, list):
            raise ValueError('Metadata changes must be a list.')
        if not additional_filter and not changes:
            raise ValueError('Metadata must contain a non-empty changes list.')
        for change in changes:
            if not isinstance(change, dict):
                raise ValueError('Each change must be a dictionary.')
            for field in ('version', 'description'):
                if not additional_filter or field in change:
                    if not isinstance(change.get(field), str) or not change[field].strip():
                        raise ValueError(f'Change field {field!r} must be a non-empty string.')
        if not additional_filter and not any(change['version'] == metadata['version'] for change in changes):
            raise ValueError('changes must include the current config version.')
    if 'basis_type' in metadata and metadata['basis_type'] not in INV_BASIS_TYPES:
        raise ValueError(f'Unrecognised metadata basis_type: {metadata["basis_type"]}.')
    if 'internal_identifiers' in metadata:
        identifiers = metadata['internal_identifiers']
        if not isinstance(identifiers, list) or any(not isinstance(v, str) or not v.strip() for v in identifiers):
            raise ValueError('internal_identifiers must be a list of non-empty strings.')
    try:
        json.dumps(metadata, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError('Metadata must be JSON serializable with finite numbers.') from error


def read_config_metadata(file_path):
    """
    Return embedded metadata for NPZ, YAML, CSV or AVRO files.

    Return {} when metadata is absent. Deprecated DR3 XML filters, supported
    only through load_additional_systems, also return {}.

    Returned dictionaries are independent. Malformed or unsupported metadata raises
    ValueError. Missing files raise FileNotFoundError. No metadata is inferred from names.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f'Configuration file not found: {path}')
    suffix = path.suffix.lower()
    metadata = None
    present = False
    if suffix == '.npz':
        with np.load(path, allow_pickle=False) as data:
            present = NPZ_METADATA_KEY in data.files
            if present:
                value = data[NPZ_METADATA_KEY]
                if value.ndim != 0 or value.dtype.kind != 'U':
                    raise ValueError('NPZ metadata must be a scalar JSON string.')
                metadata = json.loads(value.item())
    elif suffix in YAML_EXTENSIONS:
        with path.open(encoding='utf-8') as stream:
            data = yaml.load(stream, Loader=getattr(yaml, 'CSafeLoader', yaml.SafeLoader))
        if isinstance(data, dict):
            present = METADATA_KEY in data
            metadata = data.get(METADATA_KEY)
    elif suffix == '.csv':
        with path.open(encoding='utf-8') as stream:
            for line in stream:
                if not line.startswith('#'):
                    break
                if line.startswith(CSV_METADATA_PREFIX):
                    if present:
                        raise ValueError('Duplicate CSV metadata headers.')
                    present = True
                    metadata = json.loads(line[len(CSV_METADATA_PREFIX):])
    elif suffix == '.avro':
        from fastavro import reader
        with path.open('rb') as stream:
            header = reader(stream).metadata
            present = METADATA_KEY in header
            if present:
                metadata = json.loads(header[METADATA_KEY])
    elif suffix == '.xml':
        # Deprecated DR3 XML filters are supported only as additional systems.
        # They do not carry metadata.
        return {}
    else:
        raise ValueError(f'Unsupported metadata file format: {suffix}')
    if not present:
        return {}
    return metadata
