from configparser import ConfigParser
from os.path import abspath, dirname, join

config_path = abspath(dirname(__file__))
filters_path = join(config_path, 'filters')

config_ini_file = join(config_path, 'config.ini')
configparser = ConfigParser()
configparser.read(config_ini_file)
optimised_bases_file = join(config_path, configparser.get('converter', 'optimised_bases'))

correction_tables_path = join(config_path, 'correction_tables')