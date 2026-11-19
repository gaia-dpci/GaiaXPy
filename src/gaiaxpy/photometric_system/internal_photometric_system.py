"""Load the filter data shared by regular and standardised photometric systems.

Each instance selects one filter file and reads its bands, zero points,
offsets, and embedded metadata.
Filter versions are kept separate from the GaiaXPy package version.
"""
import os
import re
from copy import deepcopy
from os.path import isfile
from pathlib import Path
from typing import Optional

import numpy as np
import yaml

from gaiaxpy.core.release_resolution import parse_release

try:
    _YAML_SAFE_LOADER = yaml.CSafeLoader
except AttributeError:  # pragma: no cover - depends on PyYAML build
    _YAML_SAFE_LOADER = yaml.SafeLoader


def _safe_load_yaml(stream):
    """Parse a YAML stream using the available PyYAML safe loader."""
    return yaml.load(stream, Loader=_YAML_SAFE_LOADER)


from gaiaxpy.config.paths import config_yaml_file
from gaiaxpy.core.config_metadata import read_config_metadata
from gaiaxpy.core.utils import get_file_root, parse_array, get_array_text
from .config import load_config, _public_identifier, _additional_system_label
from .utils import _get_system_label
from ..core.config_dispatcher import GeneratorDispatcher
from ..core.generic_variables import RELEASES, ADDITIONAL_SYSTEM_PREFIX, YAML_EXTENSIONS


class InternalPhotometricSystem:
    """Hold one filter's identity, configuration arrays and optional metadata.

    name is the base name used for system classification. label is used in
    photometry column names and includes the version for additional systems.
    external_name is the public identifier, including USER, release and version
    for an additional system. Built-in naming conventions remain unchanged.
    """

    def __init__(self, name: str, is_builtin: bool, release: str, config_file: Optional[str] = None,
                 bp_model: str = 'v375wi', rp_model: str = 'v142r'):
        """Select a filter file and load its bands, zero points and corrections.

        Args:
            name (str): Base system name, without release or version prefixes.
            is_builtin (bool): Whether to select a bundled filter configuration.
            release (str): Gaia release, 'dr3'.
            config_file (str, pathlib.Path, mapping or None): Additional-filter
                selection configuration or snapshot. Built-in lookup uses the
                package configuration instead. None selects the default path.
            bp_model (str): Internal identifier used to locate a bundled BP
                calibration configuration. This is not a user-selectable calibration
                version; leave it at its default.
            rp_model (str): Internal identifier used to locate a bundled RP
                calibration configuration. This is not a user-selectable calibration
                version; leave it at its default.

        Raises:
            ValueError: Release is missing, a built-in release is unsupported, or
                filter metadata conflicts with the selected release or filename version.
            FileNotFoundError: The selected filter file cannot be found.

        Notes:
            Users select photometric systems through PhotometricSystem. The bp_model
            and rp_model arguments support internal configuration lookup; their labels
            are not Gaia release numbers or filter versions.

            Embedded metadata supplies the filter version when present. Additional
            files without metadata use their filename version. No package version
            is substituted and no descriptive metadata is invented. File-reading,
            metadata-validation and missing configuration-field errors are reported
            to the caller.
        """
        if release is None:
            raise ValueError('Release cannot be None')
        if release not in RELEASES and is_builtin:
            raise ValueError(f'Unrecognised value for built-in system with release: {release}')
        self.name = name
        self.is_builtin = is_builtin
        selected_filter = None if is_builtin else load_config(config_file).get('selected_filter')
        self.label = _additional_system_label(selected_filter) if selected_filter else _get_system_label(name)
        self.release = release
        config_file = config_yaml_file if not config_file else config_file
        self.config_file = config_file
        self.phot_system_file = InternalPhotometricSystem._retrieve_system_file(name=name, bp_model=bp_model,
                                                                                rp_model=rp_model, release=release,
                                                                                is_builtin=is_builtin,
                                                                                config_file=config_file)
        self.__set_version(selected_filter)
        self._yaml_config_cache = None
        self.bands = None
        self.zero_points = None
        self._load_xpzeropoint()
        self.offsets = None
        self._load_offset()
        self.__additional_prefix = self.__get_additional_prefix()
        self.__release_prefix = self.__get_release_prefix()
        self.prefix = f'{self.__additional_prefix}_{self.__release_prefix}' if self.__additional_prefix else self.__release_prefix
        self.external_name = (_public_identifier(selected_filter) if selected_filter
                              else f'{self.prefix}_{self.name}')

    def __get_additional_prefix(self) -> str:
        """Return an empty prefix for built-ins and USER for additional filters."""
        return '' if self.is_builtin else ADDITIONAL_SYSTEM_PREFIX

    def __get_release_prefix(self) -> str:
        """Return the uppercase release prefix, or an empty string if unavailable."""
        return '' if self.release is None else self.release.upper()

    def get_system_external_name(self):
        """Return the public identifier, including the additional-filter version."""
        return self.external_name

    def get_system_file(self):
        """Return the selected filter configuration path."""
        return self.phot_system_file

    def get_system_name(self):
        """Return the base system name, without the release prefix or version suffix."""
        return self.name

    def get_bands(self):
        """Return the configured band names in filter order."""
        return self.bands

    def get_offsets(self):
        """Return the per-band flux-bias offsets in filter order."""
        return self.offsets

    def get_release(self):
        """Return the selected Gaia release."""
        return self.release

    def get_system_label(self):
        """Return the column-name label, including the version for an additional system."""
        return self.label

    def get_system_prefix(self):
        """Return the release prefix, preceded by USER for an additional system."""
        return self.prefix

    def get_metadata(self):
        """Return a deep copy of the filter's embedded metadata, or an empty dictionary."""
        return deepcopy(self._metadata)

    def __set_version(self, selected_filter):
        """Read optional metadata and resolve the selected filter version.

        If metadata specifies a Gaia release, it must match the selected release.
        If both metadata and the filename specify a version, they must agree;
        labels such as 'v1' and '1' are treated as equivalent. Conflicting
        declarations raise ValueError.

        Use the metadata version when available, otherwise the filename version.
        Record where the version came from. If neither provides a version,
        leave it as None.
        """
        self._metadata = read_config_metadata(self.phot_system_file)
        metadata_version = self._metadata.get('version')
        declared_release = self._metadata.get('data_release')
        if declared_release is not None and declared_release != self.release:
            raise ValueError(f'Filter {self.phot_system_file}: metadata data_release {declared_release!r} '
                             f'conflicts with selected release {self.release!r}.')
        filename_version = selected_filter['version'] if selected_filter else None
        if not self.is_builtin and filename_version is None:
            # Support older saved configurations using the selected file's own name.
            match = re.fullmatch(r'.+\.gaiaxpy_dr\d+_([a-zA-Z0-9-]+)\.(?:xml|ya?ml)',
                                 Path(self.phot_system_file).name, re.IGNORECASE)
            filename_version = match[1] if match else None
        if metadata_version is not None and filename_version is not None:
            def version_label(value):
                """Remove a leading lowercase v only when it precedes a digit."""
                return re.sub(r'^v(?=[0-9])', '', value)

            if version_label(metadata_version) != version_label(filename_version):
                raise ValueError(f'Filter {self.phot_system_file}: metadata version {metadata_version!r} '
                                 f'conflicts with filename version {filename_version!r}.')
        self.filename_version = filename_version
        self.version = metadata_version if metadata_version is not None else filename_version
        self.version_source = ('metadata' if metadata_version is not None
                               else 'filename' if filename_version is not None else None)

    def get_zero_points(self):
        """Return the one-dimensional zero-point array in band order."""
        return self.zero_points

    def standardised_system_flux_correction(self, flux):
        """Reject direct use of the parent class's flux-correction method.

        Subclasses provide the correction or return flux unchanged.

        Raises:
            ValueError: Always; the parent class does not implement this operation.
        """
        raise ValueError('Method not implemented in parent class.')

    def standardised_system_error_correction(self, flux, error):
        """Reject direct use of the parent class's flux-error correction method.

        Raises:
            ValueError: Always; subclasses implement this operation.
        """
        raise ValueError('Method not implemented in parent class.')

    @staticmethod
    def _retrieve_system_file(name, bp_model, rp_model, release, is_builtin, config_file=None):
        """Resolve the configuration file for a built-in or additional system.

        Args:
            name (str): Base system name.
            bp_model (str): Internal identifier used to locate a bundled BP
                calibration configuration. This is not a user-selectable calibration
                version.
            rp_model (str): Internal identifier used to locate a bundled RP
                calibration configuration. This is not a user-selectable calibration
                version.
            release (str): Gaia release.
            is_builtin (bool): Select through the bundled configuration dispatcher.
            config_file (str, pathlib.Path, mapping or None): Additional-filter
                selection path or snapshot; None uses the default selection path.

        Returns:
            str: Selected filter path.

        Raises:
            ValueError: A selected record does not match the requested name/release,
                or a legacy filename cannot be parsed for the requested release.
            FileNotFoundError: The selected file or a legacy search match is missing.
            RuntimeError: A legacy directory search finds multiple matching files.

        Notes:
            Current selections use their recorded per-file paths. Older selection
            configurations can use stored mappings or recursive filename lookup.
        """

        def __find_unique_file(directory: Path, expected_filename: str, _release: str) -> Path:
            """Find exactly one legacy filter matching a name, release and v-number version.

            Search recursively, accepting XML files. Raise FileNotFoundError
            when absent, RuntimeError for multiple matches and ValueError
            for an invalid filename or release/format combination.
            """
            _release = parse_release(_release)
            parts = expected_filename.split('.gaiaxpy_', 1)
            if len(parts) != 2:
                raise ValueError("Filename must contain '.gaiaxpy_' exactly once")
            expected_prefix, suffix = parts
            suffix = suffix.replace('{release}', _release)
            match = re.match(r'(?i)^(dr\d+)_(v\d+)\.(xml|ya?ml)$', suffix)
            if match:
                release_in_name, version, extension = match.groups()
            else:
                raise ValueError(f'Could not parse additional-filter filename: {expected_filename}')

            if release_in_name != _release.lower():
                raise ValueError(
                    f'Expected an {_release.upper()} additional-filter file, got {release_in_name.upper()}.')
            expected_extensions = {'xml'}
            if extension.lower() not in expected_extensions:
                expected_extension = 'XML'
                raise ValueError(f'Additional filters for {_release.upper()} must use {expected_extension} files.')
            allowed_extension_pattern = 'xml'
            pattern = re.compile(
                rf'^{re.escape(expected_prefix)}\.gaiaxpy_{release_in_name}_{re.escape(version)}\.{allowed_extension_pattern}$',
                re.IGNORECASE
            )
            matches = []
            for root, _, files in os.walk(directory):
                for filename in files:
                    if pattern.match(filename):
                        full_path = os.path.join(root, filename)
                        matches.append(full_path)
            if len(matches) == 0:
                raise FileNotFoundError(f"No matching file for '{expected_filename}' in {directory}")
            elif len(matches) > 1:
                raise RuntimeError(f"Multiple matching files for '{expected_filename}' found in {directory}")
            return matches[0]

        if is_builtin:
            return GeneratorDispatcher().build(systems=[name], bp_model=bp_model, rp_model=rp_model, release=release)
        else:
            sys_details = load_config(config_file)
            selected = sys_details.get('selected_filter')
            if selected is not None:
                if (selected['name'], selected['release']) != (name, release):
                    raise ValueError(f'Selected filter does not match {release}/{name}.')
                if not isfile(selected['path']):
                    raise FileNotFoundError(f"Filter file {selected['path']} not found.")
                return selected['path']
            system_files = sys_details.get('system_files') or {}
            system_file = system_files.get(release, {}).get(name)
            if system_file:
                if isfile(system_file):
                    return system_file
                raise FileNotFoundError(f'Filter file {system_file} not found.')

            # Backwards compatibility with configs created before explicit
            # system-name -> path mappings were stored. This fallback preserves
            # the previous behaviour, including duplicate detection.
            systems_dir = Path(sys_details['filters_dir'])

            if 'filters' in sys_details:
                filter_template = sys_details['filters'][release]
                version = sys_details['versions'][release]
            else:
                filter_template = sys_details['filter']
                version = sys_details['version']
            system_filename = filter_template.replace('{version}', version).replace('{system}', name)
            system_file = __find_unique_file(systems_dir, system_filename, release)
            if isfile(system_file):
                return system_file
            else:
                raise FileNotFoundError(f'Filter file {system_file} not found.')

    def _load_offset(self):
        """Load per-band flux-bias offsets using the selected XML or YAML format."""
        if str(self.phot_system_file).lower().endswith(YAML_EXTENSIONS):
            self._load_offset_from_yaml()
        else:
            self._load_offset_from_xml()

    def _load_xpzeropoint(self):
        """Load zero points and band names using the selected XML or YAML format."""
        if str(self.phot_system_file).lower().endswith(YAML_EXTENSIONS):
            self._load_xpzeropoint_from_yaml()
        else:
            self._load_xpzeropoint_from_xml()

    def _load_config_from_yaml(self):
        """Return the cached YAML config mapping, reading the selected file as needed.

        The config section is used when present; otherwise the top-level mapping is
        used. File-reading and YAML-parsing errors are reported to the caller.
        """
        with open(self.phot_system_file) as f:
            if self._yaml_config_cache is None:
                data = _safe_load_yaml(f)
                self._yaml_config_cache = data.get('config', data)
        return self._yaml_config_cache

    def _load_offset_from_yaml(self):
        """Store YAML fluxBias values as a floating-point array in self.offsets."""
        config = self._load_config_from_yaml()
        self.offsets = np.array([float(value) for value in config['fluxBias']])

    def _load_xpzeropoint_from_yaml(self):
        """Store YAML zero points as floats and bands in their configured order."""
        config = self._load_config_from_yaml()
        self.zero_points = np.array([float(value) for value in config['zeropoints']])
        bands = config['bands']
        self.bands = bands.get('values', bands) if isinstance(bands, dict) else bands

    def _load_offset_from_xml(self):
        """Store XML fluxBias values in self.offsets."""
        x_root = get_file_root(self.phot_system_file)
        self.offsets = parse_array(x_root, 'fluxBias')

    def _load_xpzeropoint_from_xml(self):
        """Store XML zeropoints and bands in self.zero_points and self.bands."""
        x_root = get_file_root(self.phot_system_file)
        self.zero_points = parse_array(x_root, 'zeropoints')
        self.bands, _ = get_array_text(x_root, 'bands')
