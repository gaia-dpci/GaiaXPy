from configparser import ConfigParser
from os.path import abspath, dirname, join

config_path = abspath(dirname(__file__))
filters_path = join(config_path, 'filters')

config_ini_file = join(config_path, 'config.ini')
configparser = ConfigParser()
configparser.read(config_ini_file)
hermite_bases_file = join(config_path, configparser.get('converter', 'hermite_bases'))
spline_bases_file = join(config_path, configparser.get('converter', 'spline_bases'))

correction_tables_path = join(config_path, 'correction_tables')
