"""
photometric_system.py
====================================
Module for the management of photometric systems.
"""

from os.path import exists

from aenum import Enum, extend_enum

from gaiaxpy.core.generic_functions import _get_built_in_systems, _is_built_in_system
from .config import _CFG_FILE_PATH, get_yes_no_answer, create_config, get_additional_filters_names
from .regular_photometric_system import RegularPhotometricSystem
from .standardised_photometric_system import StandardisedPhotometricSystem


def _get_available_systems(config_file=None):
    """
    Get the available photometric systems according to the
    package configuration.

    Returns:
        str: A string containing the names of the photometric
             systems separated by spaces.
    """
    built_in_systems = _get_built_in_systems()
    # Try to load the configuration and see whether more systems have been defined
    additional_systems = get_additional_filters_names(config_file)
    return built_in_systems + additional_systems


class AutoName(Enum):

    def get_system_name(self):
        return self.name

    def get_system_label(self):
        return self.value.label

    def get_zero_points(self):
        return self.value.zero_points

    def get_bands(self):
        return self.value.bands

    def get_offsets(self):
        return self.value.offsets

    def get_filter_version(self):
        # TODO: Does not currently work
        return self.value.version


def _system_is_standard(system_name):
    """
    Tell whether the input system is standard or not.

    Args:
        system_name (str): Photometric system name.

    Returns:
        bool: True is system is standard, false otherwise.
    """

    return system_name.split('_')[-1].lower() == 'std'


def create_system(name, systems_path=None):
    if _system_is_standard(name):
        return StandardisedPhotometricSystem(name)
    else:
        return RegularPhotometricSystem(name, systems_path)


def get_available_systems():
    systems_list = _get_available_systems()
    return ', '.join(systems_list)


system_tuples = [(s, create_system(s, None)) if _is_built_in_system(s) else (s, create_system(s, _CFG_FILE_PATH))
                 for s in _get_available_systems(_CFG_FILE_PATH)]
PhotometricSystem = AutoName('PhotometricSystem', system_tuples)
PhotometricSystem.get_available_systems = get_available_systems


def load_additional_systems(_filters_path=None):
    """
    Load additional photometric systems.

    Args:
        _filters_path (str): Path to directory containing the additional filter files.
        config_file (str): Path to configuration file where the path to the additional filter files will be stored.
    """
    config_file = _CFG_FILE_PATH
    __load_additional_systems(_filters_path, config_file)


def __load_additional_systems(_filters_path=None, config_file=None):
    """
    Load additional photometric systems.

    Args:
        _filters_path (str): Path to directory containing the additional filter files.
        config_file (str): Path to configuration file where the path to the additional filter files will be stored.
    """
    config_file = _CFG_FILE_PATH if not config_file else config_file
    if exists(config_file):
        print('A path for additional filters has already been defined.')
        get_yes_no_answer('Do you want to redefine the path? [y/n]: ', create_config, None)
    else:
        create_config(_filters_path, config_file)
    # Re-create AutoEnum
    global PhotometricSystem
    new_system_tuples = [(s, create_system(s, config_file)) for s in _get_available_systems(config_file) if not
    _is_built_in_system(s)]
    for name, value in new_system_tuples:
        extend_enum(PhotometricSystem, name, value)
