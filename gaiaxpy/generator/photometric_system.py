"""
photometric_system.py
====================================
Module for the management of photometric systems.
"""

from configparser import ConfigParser
from os import remove
from os.path import exists

from aenum import Enum

from gaiaxpy.core.generic_functions import _get_built_in_systems, _is_built_in_system
from .config import _CFG_FILE_PATH, create_config, get_additional_filters_names, contains_filter_key
from .regular_photometric_system import RegularPhotometricSystem
from .standardised_photometric_system import StandardisedPhotometricSystem
from .utils import get_yes_no_answer


def get_available_systems():
    systems_list = _get_available_systems()
    return ', '.join(systems_list)


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

    def get_version(self):
        return self.value.version


def _system_is_standard(system_name):
    """
    Tell whether the input system is standard or not.

    Args:
        system_name (str): Photometric system name.

    Returns:
        bool: True is system is standard, false otherwise.
    """
    std_substring = system_name.split('_')[-1] if _is_built_in_system(system_name) else system_name[-3:]
    return std_substring.lower() == 'std'


def create_system(name, systems_path=None):
    return StandardisedPhotometricSystem(name, systems_path) if _system_is_standard(name) \
        else RegularPhotometricSystem(name, systems_path)


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


def _get_system_tuples():
    return [(s, create_system(s, None)) if _is_built_in_system(s) else (s, create_system(s, _CFG_FILE_PATH)) for s in
            _get_available_systems(_CFG_FILE_PATH)]


system_tuples = _get_system_tuples()
PhotometricSystem = AutoName('PhotometricSystem', system_tuples)
PhotometricSystem.get_available_systems = get_available_systems


def get_current_filters_path():
    _config_parser = ConfigParser()
    _config_parser.read(_CFG_FILE_PATH)
    return _config_parser['filter']['filters_dir']


def load_additional_systems(_systems_path=None):
    """
    Load additional photometric systems.

    Args:
        _systems_path (str): Path to directory containing the additional filter files. If not provided, the program
        will ask the user to input one.

    Returns:
        Enum: PhotometricSystem object corresponding to an enumeration of the updated available systems.
    """
    updated_enum = __load_additional_systems(_systems_path, _CFG_FILE_PATH)
    updated_enum.get_available_systems = get_available_systems
    print("Systems loaded. Use PhotometricSystem.get_available_systems() to get the names of the current available systems.")
    return updated_enum


def __load_additional_systems(_filters_path=None, config_file=None):
    """
    Load additional photometric systems. These name of these additional systems will start with the prefix USER.

    Args:
        _filters_path (str): Path to directory containing the additional filter files.
        config_file (str): Path to configuration file where the path to the additional filter files will be stored.
    """
    config_file = config_file if config_file else _CFG_FILE_PATH
    if exists(config_file) and contains_filter_key(config_file):
        print(f'A path for additional filters has already been defined. The current path is '
              f'{get_current_filters_path()}')
        get_yes_no_answer('Do you want to redefine the path? [[y]/n]: ', yes_action=create_config, no_action=None,
                          yes_args=_filters_path)
    else:
        create_config(_filters_path, config_file)
    return AutoName('PhotometricSystem', _get_system_tuples())


def remove_additional_systems():
    """
    Remove previously loaded additional photometric systems. If no additional systems have been added, no changes will
    be made.

    Returns:
        Enum: PhotometricSystem object corresponding to an enumeration of the updated available systems.
    """
    if exists(_CFG_FILE_PATH):
        remove(_CFG_FILE_PATH)
        print('Additional systems configuration successfully removed.')
    else:
        print('No additional configuration exists.')
    _PhotometricSystem = AutoName('PhotometricSystem', _get_system_tuples())
    _PhotometricSystem.get_available_systems = get_available_systems
    return _PhotometricSystem
