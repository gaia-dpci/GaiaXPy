"""Expose photometric systems through a stable registry with enum-like members.

Built-ins use identifiers such as DR3_GaiaVega. Additional filters always use
USER, the release, system name and version, such as USER_DR3_Example_v1.
Loading replaces the additional selection after validation.
"""

from copy import deepcopy
from os import remove, replace
from os.path import exists
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import wrap
from types import MappingProxyType

from aenum import Enum

from .config import _CFG_FILE_PATH, create_config, get_additional_filter_records, load_config, _public_identifier
from .utils import get_yes_no_answer, _get_built_in_systems_base_names
from ..core.generic_variables import RELEASES, ADDITIONAL_SYSTEM_PREFIX


def get_available_systems():
    """Return current public system identifiers in a grouped display string."""
    return PhotometricSystem.get_available_systems()


class AutoName(Enum):
    """Provide enum members backed by lazily loaded photometric-system descriptors.

    name is the public identifier and value is the descriptor. Member methods
    expose the selected filter's bands, zero points, version and metadata.
    """

    def get_system_name(self):
        """Return this member's public identifier, including release and any USER/version parts."""
        return self.name

    def get_system_label(self):
        """Return the column-name label, including the version for an additional system."""
        return self.value.label

    def get_zero_points(self):
        """Return the selected filter's zero-point array in band order."""
        return self.value.zero_points

    def get_bands(self):
        """Return the selected filter's band names in configuration order."""
        return self.value.bands

    def get_offsets(self):
        """Return the selected filter's per-band flux-bias offsets."""
        return self.value.offsets

    def get_version(self):
        """Return the selected filter version, independently of the package version.

        Returns:
            str: Embedded metadata version when present, otherwise the additional
            filter's filename version. The original label spelling is retained.

        Raises:
            ValueError: The selected filter has no version information.
        """
        v = self.value.version
        if v is None:
            raise ValueError('No version should be None for a built-in photometric filter.')
        return v

    def get_metadata(self):
        """Return a deep copy of the selected filter's embedded metadata.

        A filter without embedded metadata returns an empty dictionary. Filename
        versions are available separately and are not inserted into this dictionary.
        """
        return self.value.get_metadata()

    def get_system_full_label(self):
        """Return the release-prefixed column label, including USER and version when applicable."""
        return f'{self.value.get_system_prefix()}_{self.value.get_system_label()}'

    def __str__(self):
        """Return the attribute-style name, for example PhotometricSystem.DR3_GaiaVega."""
        return f'PhotometricSystem.{self.name}'

    def __repr__(self):
        """Return the public member name and its underlying descriptor representation."""
        return f'<PhotometricSystem.{self.name}: {self.value!r}>'

    def __reduce_ex__(self, protocol):
        # Store the descriptor rather than its transient enum class or cached arrays.
        """Pickle the system identity and selection descriptor rather than cached filter arrays."""
        value = self.value
        return (_restore_system, (self.name, value.name, value.is_builtin, value.release, value.systems_path))


def _restore_system(public_name, name, is_builtin, release, systems_path):
    """Restore a pickled system, reusing the current member if its descriptor matches.

    If the system is no longer selected, create a separate member retaining the
    saved descriptor. This detached member cannot be selected for generation;
    restoring it does not change the registry selection.
    """
    current = PhotometricSystem.__members__.get(public_name)
    if current is not None:
        value = current.value
        if (value.name, value.is_builtin, value.release, value.systems_path) == (
                name, is_builtin, release, systems_path):
            return current
    cls = StandardisedPhotometricSystem if _system_is_standard(name) else RegularPhotometricSystem
    value = cls(name, is_builtin, release, systems_path)
    return AutoName('_PhotometricSystemMembers', [(public_name, value)])[public_name]


def create_system(name, is_builtin, release, systems_path=None):
    """Load a regular or standardised filter from its base name and selection.

    Args:
        name (str): Base name. A case-sensitive Std suffix selects the
            standardised implementation, before any public version suffix.
        is_builtin (bool): Whether to load a bundled filter.
        release (str): Gaia release, 'dr3'.
        systems_path (str, pathlib.Path, mapping or None): Additional-filter
            selection path or snapshot. None uses the default selection path.

    Returns:
        InternalPhotometricSystem: Loaded regular or standardised implementation.
    """
    if _system_is_standard(name):
        from .standardised_photometric_system import StandardisedPhotometricSystem as _StandardisedPhotometricSystem
        return _StandardisedPhotometricSystem(name, is_builtin=is_builtin, release=release, config_file=systems_path)

    from .regular_photometric_system import RegularPhotometricSystem as _RegularPhotometricSystem
    return _RegularPhotometricSystem(name, is_builtin=is_builtin, release=release, config_file=systems_path)


class LazyPhotometricSystem:
    """Describe a selected filter and defer loading until its data are requested."""

    def __init__(self, name, is_builtin, release, systems_path=None):
        """Store the base name, origin, release and selection path or snapshot.

        No filter data are read by this constructor. systems_path may contain a
        selected_filter record identifying one additional file.
        """
        self.name = name
        self.is_builtin = is_builtin
        self.release = release
        self.systems_path = systems_path
        self._system = None

    @property
    def system(self):
        """Return the loaded implementation, creating and caching it on first access."""
        if self._system is None:
            self._system = create_system(self.name, is_builtin=self.is_builtin, release=self.release,
                                         systems_path=self.systems_path)
        return self._system

    def get_system_name(self):
        """Return the base name without release prefixes or the public version suffix."""
        return self.name

    def __getattr__(self, attr):
        """Delegate public attributes to the loaded implementation.

        Private and special attributes raise AttributeError without loading a filter.
        """
        if attr.startswith('__') and attr.endswith('__'):
            raise AttributeError(attr)

        if attr.startswith('_'):
            raise AttributeError(attr)

        return getattr(self.system, attr)


class RegularPhotometricSystem(LazyPhotometricSystem):
    """Lazy descriptor for a system whose base name does not end in Std."""
    pass


class StandardisedPhotometricSystem(LazyPhotometricSystem):
    """Lazy descriptor for a system whose base name ends in the exact suffix Std."""
    pass


def _get_system_tuples(config_file=None):
    """Build public-name/descriptor pairs for built-in and additional systems.

    Args:
        config_file (str, pathlib.Path, mapping or None): Additional selection
            path or snapshot; None uses the default selection path.

    Returns:
        list[tuple]: Public identifiers paired with lazy descriptors. Additional
        descriptors keep their own copied filter record, including the version.
    """
    tuples = []

    for release, systems in _get_available_systems(config_file).items():
        for system in systems:
            if release == ADDITIONAL_SYSTEM_PREFIX:
                name, system_release = system['name'], system['release']
                is_builtin = False
                enum_name = _public_identifier(system)
                systems_path = {'selected_filter': deepcopy(system)}
            else:
                name = system
                system_release = release
                is_builtin = True
                enum_name = f"{system_release.upper()}_{name}"
                systems_path = None

            cls = (StandardisedPhotometricSystem if _system_is_standard(name) else RegularPhotometricSystem)

            tuples.append((
                enum_name,
                cls(name=name, is_builtin=is_builtin, release=system_release, systems_path=systems_path),
            ))

    return tuples


def _get_available_systems(config_file=None):
    """Return built-in base names by release and additional records under USER.

    Args:
        config_file (str, pathlib.Path, mapping or None): Additional selection
            path or snapshot; None uses the default selection path.

    Returns:
        dict: dr3 map to lists of built-in base names; USER maps to
        per-file additional-filter records.
    """
    return {RELEASES.dr3: _get_built_in_systems_base_names(release=RELEASES.dr3),
            ADDITIONAL_SYSTEM_PREFIX: get_additional_filter_records(config_file)}


def _system_is_standard(system_name):
    """Return whether the base system name ends with the case-sensitive suffix Std.

    Supply the base name, without a public release prefix or version suffix.
    """
    return system_name.endswith('Std')


class _GroupedSystemNames(str):
    """Display grouped system names and support case-insensitive group lookup."""

    def __new__(cls, text, groups=None):
        result = super().__new__(cls, text)
        result._groups = {name.casefold(): tuple(members) for name, members in (groups or {}).items()}
        return result

    def __getitem__(self, key):
        if isinstance(key, str):
            return list(self._groups[key.casefold()])
        return super().__getitem__(key)

    def _repr_pretty_(self, printer, cycle):
        printer.text(str(self))


class PhotometricSystemRegistry:
    """Provide stable, read-only access to the currently available systems.

    Access members as attributes or by name, iterate over them, or inspect
    __members__. Attribute names appear in dir() for tab completion.

    Additional identifiers always include a version. Previously stored additional
    members are no longer valid selections after removal or replacement.
    """

    def __init__(self):
        """Create the built-in member objects and initialise the current selection to built-ins."""
        systems = AutoName('_PhotometricSystemMembers', _get_system_tuples())
        self._builtins = {system.name: system for system in systems if system.value.is_builtin}
        self._selection = (dict(self._builtins), None)

    @property
    def _members(self):
        """Return the current name-to-member mapping."""
        return self._selection[0]

    @property
    def _config_file(self):
        """Return the active additional-selection configuration path, or None."""
        return self._selection[1]

    def __setattr__(self, name, value):
        """Allow internal state updates and reject assignment to public attributes."""
        if not name.startswith('_'):
            raise AttributeError('PhotometricSystem is managed by the loading functions.')
        object.__setattr__(self, name, value)

    @property
    def __members__(self):
        """Return a read-only view of the current name-to-member mapping."""
        return MappingProxyType(self._members)

    def __getattr__(self, name):
        """Look up a current member by attribute name; raise AttributeError if absent."""
        try:
            return self._members[name]
        except KeyError:
            raise AttributeError(name) from None

    def __dir__(self):
        """Include current system identifiers in attribute discovery and tab completion."""
        return sorted(set(super().__dir__()) | self._members.keys())

    def __getitem__(self, name):
        """Look up a current member by public identifier; raise KeyError if absent."""
        return self._members[name]

    def __iter__(self):
        """Iterate over members in the current selection order."""
        return iter(self._members.values())

    def __reversed__(self):
        """Iterate over a snapshot of the current members in reverse order."""
        return reversed(tuple(self._members.values()))

    def __len__(self):
        """Return the number of currently available members."""
        return len(self._members)

    def __contains__(self, system):
        """Return whether this exact member object belongs to the current selection."""
        return isinstance(system, AutoName) and self._members.get(system.name) is system

    def __instancecheck__(self, system):
        """Accept only member objects belonging to the current selection."""
        return system in self

    def __call__(self, value):
        """Find a current member by descriptor identity, raising ValueError if absent."""
        for system in self:
            if system.value is value:
                return system
        raise ValueError(f'{value!r} is not a current PhotometricSystem value.')

    def __reduce__(self):
        """Pickle a reference to the shared registry rather than copying its selection."""
        return (_get_registry, ())

    def get_available_systems(self, *, grouped: bool = True) -> str:
        """Return current public identifiers under DR3, and Additional systems.
        In grouped mode, index by a case-insensitive group name (such as
        'dr3') to get a list of identifiers. 'Additional systems' gives an empty
        list when none are loaded. Set grouped=False for a comma-separated string.
        """
        u_dr3 = RELEASES.dr3.upper()
        members = self._members
        if not grouped:
            return ', '.join(members)
        groups = {u_dr3: [], ADDITIONAL_SYSTEM_PREFIX: []}
        for name in members:
            groups[name.partition('_')[0]].append(name)
        headings = {
            u_dr3: u_dr3,
            ADDITIONAL_SYSTEM_PREFIX: 'Additional systems'
        }
        display = '\n\n'.join(
            f'{heading}:\n' + '\n'.join(wrap(
                ', '.join(groups[prefix]), initial_indent='    ', subsequent_indent='    ',
                break_long_words=False, break_on_hyphens=False
            ))
            for prefix, heading in headings.items() if groups[prefix]
        )
        return _GroupedSystemNames(display, {heading: groups[prefix] for prefix, heading in headings.items()})


def _get_registry():
    """Return the shared PhotometricSystem registry when unpickling."""
    return PhotometricSystem


PhotometricSystem = PhotometricSystemRegistry()


def get_current_filters_path():
    """Return the selected additional-filter file or directory path.

    For older configurations, return filters_dir. If there is no readable
    selection configuration, the file-reading error is reported to the caller.
    """
    config = load_config(PhotometricSystem._config_file or _CFG_FILE_PATH)
    return config.get('selection_path', config['filters_dir'])


def load_additional_systems(_systems_path=None):
    """Load a file or directory of additional filters into PhotometricSystem.

    Args:
        _systems_path (str, pathlib.Path or None): Single filter file or directory
            searched recursively. If omitted, prompt for a path. Supported names
            are <system>.gaiaxpy_dr3_<version>.xml, ignoring case.

    Returns:
        PhotometricSystemRegistry: The shared PhotometricSystem object with the
        accepted selection. Reassigning the return value is optional.

    Raises:
        ValueError: The path, naming convention, release/format combination,
            identities or filter configuration are invalid. Duplicate identities
            and public-name or column-label collisions are rejected.
        OSError: A selected filter or selection configuration cannot be read or
            written.

    Notes:
        If additional systems are already loaded, prompt before replacing them.
        An accepted selection replaces all previous additional systems and
        retains built-ins. Failed validation leaves the previous selection usable.
        Unrelated directory files are ignored with a warning printed to stderr; an
        explicitly selected file must be supported. Filter files are not modified.

        Each additional identifier includes USER, release, name and version,
        for example PhotometricSystem.USER_DR3_Example_v1. There are no
        unversioned aliases. Multiple versions can coexist. Metadata is optional
        for additional filters; their origin does not affect loading.
    """
    registry = __load_additional_systems(_systems_path, _CFG_FILE_PATH)
    print('Systems loaded. Use PhotometricSystem.get_available_systems() to get the names of the current available'
          ' systems.')
    return registry


def __load_additional_systems(_filters_path=None, config_file=None):
    """Load into the shared registry, prompting before replacing an active selection.

    Args:
        _filters_path (str, pathlib.Path or None): File or recursive directory
            selection; None prompts for a path when replacement proceeds.
        config_file (str or pathlib.Path or None): Selection configuration
            destination; None uses the default temporary configuration path.

    Returns:
        PhotometricSystemRegistry: The shared registry. Declining replacement
        leaves its selection unchanged.
    """
    config_file = config_file if config_file else _CFG_FILE_PATH
    if PhotometricSystem._config_file is not None:
        print(f'A path for additional filters has already been defined. The current path is '
              f'{get_current_filters_path()}')
        get_yes_no_answer('Do you want to redefine the path? [[y]/n]: ',
                          yes_action=lambda: _replace_additional_systems(_filters_path, config_file),
                          no_action=None)
    else:
        _replace_additional_systems(_filters_path, config_file)
    return PhotometricSystem


def _replace_additional_systems(filters_path, config_file):
    # Stage both the configuration and system objects before publishing either.
    """Validate and load a complete selection before publishing its configuration.

    Stage the selection YAML and eagerly load each additional filter. After all
    checks pass, replace the configuration file and registry selection, retaining
    built-in members. A failure before publication leaves the previous selection
    and configuration intact. Temporary staging files are removed on exit.
    """
    target = Path(config_file)
    with TemporaryDirectory(prefix='gaiaxpy-systems-', dir=target.parent) as staging:
        staged_config = Path(staging) / 'systems.yaml'
        create_config(filters_path, str(staged_config))
        snapshot = load_config(str(staged_config))
        systems = AutoName('_PhotometricSystemMembers', _get_system_tuples(snapshot))
        members = dict(PhotometricSystem._builtins)
        for system in systems:
            if not system.value.is_builtin:
                # Check additional files before publishing the new selection.
                system.value.system
                members[system.name] = system
        replace(staged_config, target)
    PhotometricSystem._selection = (members, str(target))


def remove_additional_systems():
    """Remove the additional selection and its generated configuration file.

    Returns:
        PhotometricSystemRegistry: The same registry exposing only built-ins;
        reassignment is optional.

    Notes:
        Filter files are not deleted. Previously stored additional members are no
        longer accepted for generation. Their names disappear from registry
        lookup and tab completion.
        A status message is printed whether or not a configuration exists.
    """
    config_file = PhotometricSystem._config_file or _CFG_FILE_PATH
    if exists(config_file):
        remove(config_file)
        print('Additional systems configuration successfully removed.')
    else:
        print('No additional configuration exists.')
    PhotometricSystem._selection = (dict(PhotometricSystem._builtins), None)
    return PhotometricSystem
