from os import walk
from os.path import isdir
from pathlib import Path
from re import match

_CFG_FILE_PATH = Path('~/.gaiaxpyrc').expanduser()


class GenCfg:

    def __init__(self, filters_dir, version):
        if not isdir(filters_dir):
            raise ValueError(f'{filters_dir} is not a path to a valid directory.')
        self.filters_dir = filters_dir
        self.version = version
        self.filter = 'system.gaiaXPy_dr3_version.xml'


def get_file_names_recursively(dir_path):
    all_files = [f for _, _, fn in walk(dir_path) for f in fn]
    return [f for f in all_files if file_name_is_compliant(f)]


def file_name_is_compliant(file_name):
    regex = '[a-zA-Z0-9-_]+\.gaiaXPy_dr3_[a-zA-Z0-9-]+\.xml'
    return match(regex, file_name) is not None
