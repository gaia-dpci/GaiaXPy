"""Discover additional filter files and save their paths and identities.

Accept a single filter file or search a directory recursively. Additional-filter
filenames identify the system name, Gaia release and version.

The generated YAML configuration records the selected filters and their paths.
The supplied filter files are not copied or modified.
"""
import re
import tempfile
from collections.abc import Mapping
from copy import deepcopy
from os import walk, urandom
from os.path import isdir, join
from pathlib import Path
from typing import Union

import yaml

from gaiaxpy.core.generic_functions import _warning
from gaiaxpy.core.generic_variables import RELEASES, ADDITIONAL_SYSTEM_PREFIX

try:
    _YAML_SAFE_LOADER = yaml.CSafeLoader
except AttributeError:
    _YAML_SAFE_LOADER = yaml.SafeLoader


def _safe_load_yaml(stream):
    """Parse a YAML stream using the available PyYAML safe loader."""
    return yaml.load(stream, Loader=_YAML_SAFE_LOADER)


_CFG_FILE_PATH = join(tempfile.gettempdir(), urandom(24).hex())
_FILTER_FILE_NAME_REGEX = re.compile(
    r'(?P<name>[a-zA-Z0-9_-]+)\.gaiaxpy_(?P<release>dr\d+)_(?P<version>[a-zA-Z0-9-]+)\.(?P<format>xml|ya?ml)',
    re.IGNORECASE,
)


class GenCfg:
    """Store the resolved selection path, containing directory and filter records."""

    def __init__(self, systems_path: str, file_records: list):
        """Resolve an existing file or directory and copy its filter records.

        Args:
            systems_path (str or pathlib.Path): Existing filter file or directory.
            file_records (list[dict]): Discovered filter identities and paths.

        Raises:
            ValueError: The path is neither an existing file nor a directory.

        Notes:
            filters_dir is the parent directory for a single-file selection and
            the selected directory otherwise. file_records is a deep copy.
        """
        path = Path(systems_path)
        if not (path.is_file() or path.is_dir()):
            raise ValueError(f'Additional-filter input is not an existing file or directory: {path}')
        path = path.resolve()
        self.selection_path = str(path)
        self.filters_dir = str(path.parent if path.is_file() else path)
        self.file_records = deepcopy(file_records)


def _filter_record(path):
    """Extract an additional filter identity from its filename and resolve its path.

    Args:
        path (str or pathlib.Path): Filter path. This function checks the name,
            not the file contents or whether the file exists.

    Returns:
        dict: name, lowercase release, version, filename and absolute path.

    Raises:
        ValueError: The filename does not follow
            <system>.gaiaxpy_dr3_<version>.xml. Matching ignores case,
            but system names and version labels retain their spelling.
    """
    path = Path(path)
    match = _FILTER_FILE_NAME_REGEX.fullmatch(path.name)
    if match is None:
        raise ValueError(
            f'Unsupported additional-filter filename: {path}. Expected <system>.gaiaxpy_dr3_<version>.xml.')
    fields = match.groupdict()
    release = fields['release'].lower()
    extension = fields['format'].lower()
    allowed_formats = {RELEASES.dr3: {'xml'}}
    if extension not in allowed_formats.get(release, set()):
        raise ValueError(f'Additional photometric systems must be DR3 XML filter files: {path}')
    return {'name': fields['name'], 'release': release, 'version': fields['version'],
            'filename': path.name, 'path': str(path.resolve())}


def __get_file_records_recursively(dir_path: str, show_warning: bool = False) -> list:
    """Discover filter records in a directory and its subdirectories.

    Args:
        dir_path (str or pathlib.Path): Existing directory.
        show_warning (bool): Print a warning to stderr listing ignored files.

    Returns:
        list[dict]: Filter records in sorted directory and filename order.

    Raises:
        ValueError: The directory is invalid, no filters are found, or a filename
            matches the naming pattern but uses an unsupported release or format.

    Notes:
        Files outside the naming pattern are ignored. Files matching the pattern
        must use DR3 XML; they are not silently skipped.
    """
    if not isdir(dir_path):
        raise ValueError('Input path is not a valid directory.')
    records, ignored = [], []
    for root, directories, filenames in walk(dir_path):
        directories.sort()
        for filename in sorted(filenames):
            path = Path(root, filename)
            if _FILTER_FILE_NAME_REGEX.fullmatch(filename):
                records.append(_filter_record(path))
            else:
                ignored.append(str(path.resolve()))
    if ignored and show_warning:
        _warning(f'Ignoring files that do not match the additional-filter naming convention:  {", ".join(ignored)}')
    if not records:
        raise ValueError('No filter files found in the given directory. Please check your files.')
    return records


def __get_file_names_recursively(dir_path: str, show_warning: bool = False) -> list:
    """Return filenames from recursive discovery, optionally reporting ignored files."""
    return [record['filename'] for record in __get_file_records_recursively(dir_path, show_warning)]


def _discover_filter_records(systems_path):
    """Discover a file or directory selection, rejecting invalid paths.

    Directory input reports ignored files to stderr. An explicitly selected file
    must have a supported filter filename; unrelated files are not ignored.
    """
    path = Path(systems_path)
    if path.is_file():
        return [_filter_record(path)]
    if path.is_dir():
        return __get_file_records_recursively(path, show_warning=True)
    raise ValueError(f'Additional-filter input is not an existing file or directory: {path}')


def _public_identifier(record):
    """Build USER_RELEASE_NAME_VERSION for a filter record.

    Hyphens become underscores in the name and version. A version starting with
    a digit gains a leading v. Collision checks are performed separately.
    """
    name = record['name'].replace('-', '_')
    return f"{ADDITIONAL_SYSTEM_PREFIX}_{record['release'].upper()}_{name}_{_version_identifier(record['version'])}"


def _version_identifier(version):
    """Replace version-label hyphens with underscores and prefix numeric labels with v.

    Args:
        version (str): Non-empty filename version label.

    Returns:
        str: Label used in public identifiers and photometry column names.
    """
    label = version.replace('-', '_')
    return 'v' + label if label[0].isdigit() else label


def _additional_system_label(record):
    """Build a versioned column label using the existing system-name conventions."""
    from .utils import _get_system_label
    name = _get_system_label(record['name']).replace('-', '_')
    return f"{name}_{_version_identifier(record['version'])}"


def _validate_filter_records(records):
    """Reject duplicate identities and names that would produce the same identifier.

    Args:
        records (list[dict]): Filter records containing name, release, version
            and path.

    Raises:
        ValueError: Two records share a release/name/version identity, public
            identifier or photometry column label. Errors identify both paths.

    Notes:
        This checks identities and naming collisions, not filter contents.
    """
    identities, identifiers = {}, {}
    for record in records:
        identity = (record['release'], record['name'], record['version'])
        if identity in identities:
            raise ValueError(f'Duplicate additional-filter identity {identity}: '
                             f"{identities[identity]['path']} and {record['path']}")
        identities[identity] = record
        identifier = _public_identifier(record)
        if identifier in identifiers:
            raise ValueError(f'Additional-filter identifier collision for {identifier}: '
                             f"{identifiers[identifier]['path']} and {record['path']}")
        identifiers[identifier] = record

    # Current column labels may also normalise built-in spellings (e.g. JKC -> Jkc).
    labels = {}
    for record in records:
        label = (record['release'], _additional_system_label(record))
        if label in labels:
            raise ValueError(f'Additional-filter photometry label collision for {label}: '
                             f"{labels[label]['path']} and {record['path']}")
        labels[label] = record


def create_config(systems_path: Union[Path, str] = None, config_file: str = None):
    """Discover and validate a filter selection, then write its configuration.

    Args:
        systems_path (str, pathlib.Path or None): Single filter file or directory
            to search recursively. If omitted or empty, prompt for a path.
            Matching outer quotes are removed from the supplied path.
        config_file (str or pathlib.Path or None): Selection YAML destination.
            None uses this process's default temporary configuration path.

    Raises:
        ValueError: The selection path, filenames or identities are invalid.
        OSError: The selection configuration cannot be written.

    Notes:
        Discovery and identity validation finish before writing. Filter contents
        are checked later by the system loader. Existing filters are never
        modified. Writing prints the number of selected filters.
    """
    if not systems_path:
        systems_path = input('Please enter the path to a system file or directory: ')
    systems_path = str(systems_path)
    if len(systems_path) >= 2 and systems_path[0] in ("'", '"') and systems_path[-1] == systems_path[0]:
        systems_path = systems_path[1:-1]
    if not systems_path:
        raise ValueError('Additional-filter input must be a file or directory path.')
    file_records = _discover_filter_records(systems_path)
    _validate_filter_records(file_records)
    cfg_details = GenCfg(systems_path, file_records)
    __write_config(cfg_details, config_file)


def __write_config(cfg_details, config_file: str = None):
    """Write selection details as YAML and print the filter count.

    Args:
        cfg_details (GenCfg): Resolved paths and filter records to write.
        config_file (str or pathlib.Path or None): Destination, or None for the
            process's default temporary configuration path.
    """
    config_file = _CFG_FILE_PATH if not config_file else config_file
    config = vars(cfg_details)
    with open(config_file, 'w') as cf:
        yaml.safe_dump(config, cf)
    print(f'Loading {len(cfg_details.file_records)} additional photometric system(s).')


def load_config(config_file: Union[Path, str, Mapping] = None):
    """Read a selection configuration or copy an in-memory snapshot.

    Args:
        config_file (str, pathlib.Path, collections.abc.Mapping or None): YAML
            path or configuration snapshot. None uses the process's default
            temporary configuration path.

    Returns:
        dict: Parsed YAML configuration, or a deep copy of a supplied mapping.

    Notes:
        File-reading and YAML-parsing errors are reported to the caller. This
        function does not validate the configuration's structure.
    """
    if isinstance(config_file, Mapping):
        return deepcopy(dict(config_file))
    config_file = _CFG_FILE_PATH if not config_file else config_file
    with open(config_file) as f:
        config = _safe_load_yaml(f)
    return config


def get_additional_filters_path(config_file: str = None):
    """Return the containing directory recorded in the selection configuration.

    Args:
        config_file (str, pathlib.Path, collections.abc.Mapping or None): Selection
            configuration; None uses the process's default configuration path.

    Returns:
        str or None: Recorded filters_dir, or None if the file cannot be read or
        the key is missing. A single-file selection returns its parent directory.
    """
    try:
        config = load_config(config_file)
        return config['filters_dir']
    except (IOError, KeyError):
        return None


def contains_filter_key(config_file: str = None):
    """Check whether a loaded selection has a non-empty filters_dir value.

    Args:
        config_file (str, pathlib.Path, collections.abc.Mapping or None): Selection
            configuration; None uses the process's default configuration path.

    Returns:
        bool: Whether filters_dir is present and truthy.

    Notes:
        A missing key returns False. Errors while opening or parsing the
        configuration are reported to the caller.
    """
    config = load_config(config_file)
    try:
        k = bool(config['filters_dir'])
    except (IOError, KeyError):
        return False
    return k


def get_additional_filter_records(config_file=None):
    """Read individual filter identities and paths from a selection configuration.

    Args:
        config_file (str, pathlib.Path, collections.abc.Mapping or None): Selection
            configuration; None uses the process's default configuration path.

    Returns:
        list[dict]: Per-file records, or an empty list if the configuration
        cannot be read or contains no filter paths.
    """
    try:
        config = load_config(config_file)
    except IOError:
        return []
    if 'file_records' in config:
        return config['file_records']
    # Read earlier configuration snapshots without exposing unversioned aliases.
    system_files = config.get('system_files') or {}
    if system_files:
        return [_filter_record(path) for files in system_files.values() for path in files.values()]
    filters_path = config.get('filters_dir')
    return __get_file_records_recursively(filters_path) if filters_path else []
