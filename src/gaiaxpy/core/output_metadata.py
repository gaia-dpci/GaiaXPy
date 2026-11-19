from pathlib import Path

from gaiaxpy.config.paths import config_path
from gaiaxpy.core.config_metadata import read_config_metadata
from gaiaxpy.core.version import __version__

OUTPUT_METADATA_KEY = 'gaiaxpy_metadata'


def collect_config_metadata(paths):
    """Describe actual configuration files once, preserving their order."""
    result = []
    seen = set()
    for path in paths:
        path = Path(path).resolve()
        if path in seen:
            continue
        seen.add(path)
        entry = {}
        try:
            entry['file'] = path.relative_to(config_path.resolve()).as_posix()
        except ValueError:
            entry['file'] = path.name
            entry['external'] = True
        entry['metadata'] = read_config_metadata(path)
        result.append(entry)
    return result


def collect_output_metadata(function, release, config_files, correction_files=(), *, basis_type=None):
    """Describe the selected files using their embedded metadata.

    Configuration paths are relative to the package config directory. Legacy files
    remain listed with empty metadata; missing metadata is never inferred.
    External files are labelled explicitly and identified by filename, without
    exposing local directory paths in output products.
    """

    def files(value):
        if isinstance(value, dict):
            for child in value.values():
                yield from files(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                yield from files(child)
        else:
            yield Path(value)

    metadata = {'schema_version': 1, 'function': function, 'gaiaxpy_version': __version__,
                'data_release': release, 'configuration_files': collect_config_metadata(files(config_files))}
    if basis_type is not None:
        metadata['basis_type'] = basis_type
    return metadata
