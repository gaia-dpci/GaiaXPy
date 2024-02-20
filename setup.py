"""
Setup module for GaiaXPy.

Francesca De Angeli, Zuzanna Kostrzewa-Rutkowska, Paolo Montegriffo, Lovro Palaversa, Daniela Ruz-Mieres - 2024

Based on:
https://packaging.python.org/tutorials/packaging-projects
"""

from setuptools import setup, find_packages

AUTHORS = 'Francesca De Angeli, Zuzanna Kostrzewa-Rutkowska, Paolo Montegriffo, Lovro Palaversa, Daniela Ruz-Mieres'

CLASSIFIERS = ['Programming Language :: Python :: 3',
               'License :: OSI Approved :: BSD License',
               'Operating System :: OS Independent']


setup(
    name='GaiaXPy',
    use_scm_version={'write_to_template': '__version__ = "{version}"\n'},
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
    tests_require=['pytest', 'pytest-mock'],
    include_package_data=True,
    classifiers=CLASSIFIERS
)
