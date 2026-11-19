"""Resolve paths to configuration assets distributed with GaiaXPy.

Paths are absolute and are based on this module's location rather than the
current working directory. ``config_path`` is a :class:`pathlib.Path`; the
other exported paths are strings.

Attributes:
    config_path (pathlib.Path): Absolute directory containing the packaged
        ``config.yaml`` file and configuration assets.
    config_yaml_file (pathlib.Path): Absolute path to the packaged ``config.yaml`` file.
    configparser (dict): Configuration mapping read from ``config_yaml_file``
        with :func:`yaml.safe_load` when this module is imported.
    hermite_bases_file (pathlib.Path): Absolute path to the DR3 converter basis file,
        selected by the ``converter.dr3`` configuration entry.
    colour_equation_dir (pathlib.Path): Absolute directory containing the DR3 photometric
        colour-equation files, selected by the ``colour_equation.dr3``
        configuration entry. Colour equations apply to DR3 only.

Notes:
    Importing this module reads ``config.yaml`` and resolves the paths above.
    The exported values are calculated at import time. It does not load the
    referenced basis files or colour-equation files, or check that those assets
    exist. Errors encountered while reading the file, parsing YAML or accessing
    required configuration entries are raised during import.

Examples:
    Locate the directory containing the packaged filters::

        from gaiaxpy.config.paths import config_path

        filters_directory = config_path / 'filters'
"""
from os.path import abspath, dirname
from pathlib import Path

import yaml

from gaiaxpy.core.generic_variables import RELEASES

config_path = Path(abspath(dirname(__file__)))

config_yaml_file = config_path / 'config.yaml'
with open(config_yaml_file) as f:
    configparser = yaml.safe_load(f)

__converter_dr3_dict = configparser.get('converter')[RELEASES.dr3]
hermite_bases_file = config_path / __converter_dr3_dict['path'] / __converter_dr3_dict['file']

colour_equation_dir = config_path / configparser['colour_equation'][RELEASES.dr3]['path']
