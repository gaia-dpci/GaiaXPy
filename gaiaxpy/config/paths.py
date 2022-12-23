from os.path import abspath, dirname, join

config_path = abspath(dirname(__file__))
config_file = join(config_path, 'config.ini')
filters_path = join(config_path, 'filters')
