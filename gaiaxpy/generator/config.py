import sys
import tempfile
from configparser import ConfigParser
from os import walk, urandom
from os.path import isdir, join
from re import match

from gaiaxpy.core.config import ADDITIONAL_SYSTEM_PREFIX

_CFG_FILE_PATH = join(tempfile.gettempdir(), urandom(24).hex())


class GenCfg:

    def __init__(self, filters_dir: str, version: str):
        if not isdir(filters_dir):
            raise ValueError(f'{filters_dir} is not a path to a valid directory.')
        self.filters_dir = filters_dir
        self.version = version
        self.filter = 'system.gaiaXPy_dr3_version.xml'


def __get_file_names_recursively(dir_path: str, show_warning: bool = False) -> list:
    """
    Get all compliant file names recursively from a directory.

    Args:
        dir_path (str): Path to the directory where the files are located.

    Returns:
        list: List of compliant file names.

    Raises:
        ValueError: If no compliant files are found in the given directory.
    """
    all_files = [f for _, _, fn in walk(dir_path) for f in fn]
    compliant_files = [f for f in all_files if __file_name_is_compliant(f)]
    if len(compliant_files) == 0:
        raise ValueError('No filter files found in the given directory. Please check your files.')
    elif len(compliant_files) < len(all_files) and show_warning:
        message = 'Some files in the directory do not correspond to filter files. The program will ignore them.'
        print(f'UserWarning: {message}', file=sys.stderr)
    return compliant_files


def __file_name_is_compliant(file_name: str) -> bool:
    """
    Check if a file name is compliant with the naming convention.

    Args:
        file_name (str): Name of the file.

    Returns:
        bool: True if the file name is compliant, False otherwise.
    """
    regex = '[a-zA-Z0-9-_]+\.gaiaXPy_dr3_[a-zA-Z0-9-]+\.xml'
    return match(regex, file_name) is not None


def create_config(systems_path: str = None, config_file: str = None):
    """
    Creates a configuration file with the provided `systems_path` and `config_file` parameters.
    If `systems_path` is not provided, it will prompt the user to enter it.
    The configuration file contains the path to the additional systems directory and the version of the additional
    systems. If more than one version of the additional systems is detected, a ValueError will be raised.

    Args:
        systems_path (str): The path to the additional systems' directory. If not provided, it will be prompted.
        config_file (str): The path to the configuration file. If not provided, the default path will be used.
    """
    quotes = ["'", '"']
    if not systems_path:
        systems_path = input('Please enter the path to the systems directory: ')
    systems_path = systems_path[1:-1] if systems_path[0] in quotes and systems_path[-1] in quotes else systems_path
    # Get filters version
    files = __get_file_names_recursively(systems_path, show_warning=True)
    version = [f.split('.')[1].split('_')[-1] for f in files]
    if len(set(version)) != 1:
        raise ValueError('More than one version detected in the additional systems. This is currently not allowed.')
    elif len(set(version)) == 1:
        version = version[0]
    cfg_details = GenCfg(systems_path, version)
    __write_config(cfg_details, config_file)


def __write_config(cfg_details, config_file: str = None):
    """
    Write the configuration details to the config file.

    Args:
        cfg_details: Object with the configuration details.
        config_file (str): Path to the config file. Defaults to None.
    """
    config_file = _CFG_FILE_PATH if not config_file else config_file
    config = ConfigParser()
    config['filter'] = vars(cfg_details)
    with open(config_file, 'w') as cf:
        config.write(cf)
    print(f'Loading systems... Additional systems version is: {cfg_details.version}.')


def load_config(config_file: str = None):
    """
    Load the configuration file and return a ConfigParser object containing the parsed data.

    Args:
        config_file (str): The path to the configuration file. Defaults to None, which uses the default configuration
            file.

    Returns:
        ConfigParser: A ConfigParser object containing the parsed configuration data.
    """
    config_file = _CFG_FILE_PATH if not config_file else config_file
    config = ConfigParser()
    with open(config_file) as f:
        config.read_file(f)
    return config


def get_additional_filters_path(config_file: str = None):
    """
    Return the path to the directory containing the additional filters.

    Args:
        config_file (str): The path to the configuration file. If no path is given, the default configuration file will
            be used.

    Returns:
        str: The path to the directory containing the additional filters.
    """
    try:
        config = load_config(config_file)
        return config['filter']['filters_dir']
    except (IOError, KeyError):
        return None


def contains_filter_key(config_file: str = None):
    """
    Determine if the configuration file contains the key for the additional filters' directory.

    Args:
        config_file (str): The path to the configuration file. If no path is given, the default configuration file will
            be used.

    Returns:
        bool: True if the configuration file contains the key for the additional filters' directory, False otherwise.
    """
    config = load_config(config_file)
    try:
        k = bool(config['filter']['filters_dir'])
    except (IOError, KeyError):
        return False
    return k


def get_additional_filters_names(config_file: str = None):
    """
    Returns the names of the additional filters.

    Args:
        config_file (str): The path to the configuration file. If no path is given, the default configuration file will
            be used.

    Returns:
        list: The names of the additional filters.
    """
    filters_path = get_additional_filters_path(config_file)
    additional_system_names = []
    if filters_path:
        filenames = __get_file_names_recursively(filters_path)
        additional_system_names = [f"{ADDITIONAL_SYSTEM_PREFIX}_{f.split('.')[0]}" for f in filenames]
    return additional_system_names
