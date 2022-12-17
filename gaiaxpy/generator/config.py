from configparser import ConfigParser
from dataclasses import asdict, dataclass
from os import listdir
from os.path import isdir, isfile, join
from pathlib import Path

from gaiaxpy.core.config import _ADDITIONAL_SYSTEM_PREFIX

_CFG_FILE_PATH = Path('~/.gaiaxpyrc').expanduser()


@dataclass(frozen=True)
class GenCfg:
    filters_dir: str
    version: str
    filter: str = 'system.gaiaXPy_dr3_version.xml'

    def __post_init__(self):
        if not isdir(self.filters_dir):
            raise ValueError(f'{self.filters_dir} is not a path to a valid directory.')


def create_config(filters_path=None, config_file=None):
    if not filters_path:
        filters_path = input('Please enter the path to the filters directory: ')
    # Get filters version
    version = [f.split('.')[1].split('_')[-1] for f in listdir(filters_path) if isfile(join(filters_path, f))]
    if len(set(version)) != 1:
        raise ValueError('More than one version detected in the additional filters.')
    elif len(set(version)) == 1:
        version = version[0]
    cfg_details = GenCfg(filters_path, version)
    write_config(cfg_details, config_file)


def write_config(cfg_details, config_file=None):
    config_file = _CFG_FILE_PATH if not config_file else config_file
    config = ConfigParser()
    config['filter'] = asdict(cfg_details)
    with open(config_file, 'w') as cf:
        config.write(cf)
    print(f"Configuration saved. Filters version {cfg_details.version}.")


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
    except IOError:
        return None


def get_additional_filters_names(config_file=None):
    filters_path = get_additional_filters_path(config_file)
    if filters_path:
        filenames = [f for f in listdir(filters_path) if isfile(join(filters_path, f))]
        additional_system_names = [f"{_ADDITIONAL_SYSTEM_PREFIX}_{f.split('.')[0]}" for f in filenames]
    else:
        additional_system_names = []
    return additional_system_names


def execute_answer(action, message=None):
    if action:
        action()
        if message:
            print(message)


def get_yes_no_answer(question, yes_action, no_action, yes_message=None, no_message=None):
    yes_choices = ['yes', 'y']
    no_choices = ['no', 'n']
    while True:
        user_input = input(question)
        if user_input.lower() in yes_choices:
            execute_answer(yes_action, yes_message)
            break
        elif user_input.lower() in no_choices:
            execute_answer(no_action, no_message)
            break
        else:
            print('Please type yes or no.')
            continue
