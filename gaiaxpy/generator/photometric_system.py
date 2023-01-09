"""
photometric_system.py
====================================
Module for the management of photometric systems.
"""

from configparser import ConfigParser

from aenum import Enum

from gaiaxpy.core.generic_functions import _get_built_in_systems
from .config import _CFG_FILE_PATH
from .regular_photometric_system import RegularPhotometricSystem
from .standardised_photometric_system import StandardisedPhotometricSystem


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
    std_substring = system_name[-3:]
    return std_substring.lower() == 'std'


def create_system(name, systems_path=None):
    return StandardisedPhotometricSystem(name, systems_path) if _system_is_standard(name) \
        else RegularPhotometricSystem(name, systems_path)


def _get_available_systems():
    """
    Get the available photometric systems according to the
    package configuration.
    Returns:
        str: A string containing the names of the photometric
             systems separated by spaces.
    """
    return _get_built_in_systems()


def _get_system_tuples():
    return [(s, create_system(s, None)) for s in _get_available_systems()]


system_tuples = _get_system_tuples()
PhotometricSystem = AutoName('PhotometricSystem', system_tuples)
PhotometricSystem.get_available_systems = get_available_systems


def get_current_filters_path():
    _config_parser = ConfigParser()
    _config_parser.read(_CFG_FILE_PATH)
    return _config_parser['filter']['filters_dir']
