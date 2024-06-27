"""
Setup module for GaiaXPy.

Francesca De Angeli, Zuzanna Kostrzewa-Rutkowska, Paolo Montegriffo, Lovro Palaversa, Daniela Ruz-Mieres - 2024

Based on:
https://packaging.python.org/tutorials/packaging-projects
"""
import re
from os.path import abspath, dirname, join
from setuptools import setup, find_packages

AUTHORS = 'Francesca De Angeli, Zuzanna Kostrzewa-Rutkowska, Paolo Montegriffo, Lovro Palaversa, Daniela Ruz-Mieres'

CLASSIFIERS = ['Programming Language :: Python :: 3',
               'License :: OSI Approved :: BSD License',
               'Operating System :: OS Independent']


def get_property(prop):
    version_file_path = join(dirname(abspath(__file__)), 'src/gaiaxpy/core/version.py')
    result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open(version_file_path).read())
    return result.group(1)


setup(
    name='GaiaXPy',
    version=get_property('__version__'),
    author=AUTHORS,
    author_email='fda@ast.cam.ac.uk',
    maintainer='Daniela Ruz-Mieres',
    maintainer_email='d.ruzmieres@ast.cam.ac.uk',
    description='Utilities to handle BP/RP (XP) Gaia low-resolution spectra as delivered via the archive',
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
    url='https://gaia-dpci.github.io/GaiaXPy-website/',
    python_requires='>=3.8',
    packages=find_packages('src'),
    extras_require={'tests': ['pytest', 'pytest-mock']},
    include_package_data=True,
    classifiers=CLASSIFIERS
)
