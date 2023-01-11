import tempfile
import sys
from configparser import ConfigParser
from os import walk, urandom
from re import match
from os.path import isdir, join

from gaiaxpy.core.config import ADDITIONAL_SYSTEM_PREFIX

_CFG_FILE_PATH = join(tempfile.gettempdir(), urandom(24).hex())


class GenCfg:

    def __init__(self, filters_dir, version):
        if not isdir(filters_dir):
            raise ValueError(f'{filters_dir} is not a path to a valid directory.')
        self.filters_dir = filters_dir
        self.version = version
        self.filter = 'system.gaiaXPy_dr3_version.xml'


def get_file_names_recursively(dir_path):
    all_files = [f for _, _, fn in walk(dir_path) for f in fn]
    compliant_files = [f for f in all_files if file_name_is_compliant(f)]
    if len(compliant_files) == 0:
        raise ValueError('No system files found in the given directory. Please check your files.')
    elif len(compliant_files) < len(all_files):
        message = 'Some files in the directory do not correspond to system files. The program will ignore them.'
        print(f'UserWarning: {message}', file=sys.stderr)
    return compliant_files


def file_name_is_compliant(file_name):
    regex = '[a-zA-Z0-9-_]+\.gaiaXPy_dr3_[a-zA-Z0-9-]+\.xml'
    return match(regex, file_name) is not None


def create_config(systems_path=None, config_file=None):
    quotes = ["'", '"']
    if not systems_path:
        systems_path = input('Please enter the path to the systems directory: ')
    systems_path = systems_path[1:-1] if systems_path[0] in quotes and systems_path[-1] in quotes else systems_path
    # Get filters version
    files = get_file_names_recursively(systems_path)
    version = [f.split('.')[1].split('_')[-1] for f in files]
    if len(set(version)) != 1:
        raise ValueError('More than one version detected in the additional systems. This is currently not allowed.')
    elif len(set(version)) == 1:
        version = version[0]
    cfg_details = GenCfg(systems_path, version)
    write_config(cfg_details, config_file)


def write_config(cfg_details, config_file=None):
    config_file = _CFG_FILE_PATH if not config_file else config_file
    config = ConfigParser()
    config['filter'] = vars(cfg_details)
    with open(config_file, 'w') as cf:
        config.write(cf)
    print(f"Loading systems... Additional systems version is: {cfg_details.version}.")


def load_config(config_file=None):
    config_file = _CFG_FILE_PATH if not config_file else config_file
    config = ConfigParser()
    with open(config_file) as f:
        config.read_file(f)
    return config


def get_additional_filters_path(config_file=None):
    try:
        config = load_config(config_file)
        return config['filter']['filters_dir']
    except (IOError, KeyError):
        return None


def contains_filter_key(config_file=None):
        config = load_config(config_file)
        try:
            k =  bool(config['filter']['filters_dir'])
        except (IOError, KeyError):
            return False
        return bool(k)


def get_additional_filters_names(config_file=None):
    filters_path = get_additional_filters_path(config_file)
    if filters_path:
        filenames = get_file_names_recursively(filters_path)
        additional_system_names = [f"{ADDITIONAL_SYSTEM_PREFIX}_{f.split('.')[0]}" for f in filenames]
    else:
        additional_system_names = []
    return additional_system_names
