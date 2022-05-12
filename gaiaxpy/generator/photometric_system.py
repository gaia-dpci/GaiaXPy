"""
photometric_system.py
====================================
Module for the management of photometric systems.
"""

from enum import Enum
from configparser import ConfigParser
from re import finditer
from os import path
from .regular_photometric_system import RegularPhotometricSystem
from .standardised_photometric_system import StandardisedPhotometricSystem
from gaiaxpy.config import config_path
from gaiaxpy.core import _get_system_label

config_parser = ConfigParser()
config_parser.read(path.join(config_path, 'config.ini'))


def _system_is_standard(system_label):
    """
    Tells whether the input system is standard or not.
    """
    def split_camel_case(word):
        matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', word)
        return [m.group(0) for m in matches]
    return split_camel_case(system_label)[-1].lower() == 'std'


def _get_available_systems():
    """
    Get the available photometric systems according to the
    package configuration.

    Returns:
        str: A string containing the names of the photometric
             systems separated by spaces.
    """
    file = path.join(config_path, 'available_systems.txt')
    f = open(file, 'r')
    lines = f.read().splitlines()
    return ' '.join(lines)


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        label = _get_system_label(name)
        # Define type of object to create based on the name
        if _system_is_standard(label):
            return StandardisedPhotometricSystem(label)
        else:
            return RegularPhotometricSystem(label)

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


PhotometricSystem = AutoName('PhotometricSystem', _get_available_systems())


def get_available_systems():
    systems_str = _get_available_systems()
    return ', '.join(systems_str.split(' '))


PhotometricSystem.get_available_systems = get_available_systems
