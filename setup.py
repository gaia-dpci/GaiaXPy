"""
Setup module for GaiaXPy.

Francesca De Angeli, Zuzanna Kostrzewa-Rutkowska, Paolo Montegriffo, Lovro Palaversa, Daniela Ruz-Mieres - 2023

Based on:
https://packaging.python.org/tutorials/packaging-projects
"""
import re
from os import path

from setuptools import setup, find_packages

current_path = path.abspath(path.dirname(__file__))


def get_property(prop):
    result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open('gaiaxpy' + '/core/version.py').read())
    return result.group(1)


AUTHORS = 'Francesca De Angeli, Zuzanna Kostrzewa-Rutkowska, Paolo Montegriffo, Lovro Palaversa, Daniela Ruz-Mieres'

CLASSIFIERS = ['Programming Language :: Python :: 3',
               'License :: OSI Approved :: BSD License',
               'Operating System :: OS Independent']

INSTALL_REQUIRES = ['aenum',
                    'astropy',
                    'astroquery',
                    'fastavro',
                    'matplotlib',
                    'numpy>1.13',
                    'packaging',
                    'pandas>=1.0.0',
                    'scipy',
                    'tqdm>=4.64.0']

SETUP_REQUIRES = INSTALL_REQUIRES + ['setuptools', 'setuptools_scm', 'wheel']

EXTRAS_REQUIRE = {'tests': ['pytest', 'pytest-cov']}

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setup(
    name='GaiaXPy',
    version=get_property('__version__'),
    author=AUTHORS,
    author_email='fda@ast.cam.ac.uk',
    maintainer='Daniela Ruz-Mieres',
    maintainer_email='d.ruzmieres@ast.cam.ac.uk',
    description='Utilities to handle BP/RP (XP) Gaia low-resolution spectra as delivered via the archive',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://gaia-dpci.github.io/GaiaXPy-website/',
    python_requires='>=3.7',
    packages=find_packages(),
    install_requires=INSTALL_REQUIRES,
    include_package_data=True,
    classifiers=CLASSIFIERS
)
