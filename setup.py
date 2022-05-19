"""
Setup module for GaiaXPy.

Francesca De Angeli, Paolo Montegriffo, Lovro Palaversa, Daniela Ruz-Mieres - 2022

Based on:
https://packaging.python.org/tutorials/packaging-projects
"""
import re
from os import path
from setuptools import setup, find_packages

current_path = path.abspath(path.dirname(__file__))


def get_property(prop):
    result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open('gaiaxpy' + '/__init__.py').read())
    return result.group(1)


with open("requirements.txt") as f:
    required_packages = f.readlines()

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='GaiaXPy',
    version=get_property('__version__'),
    author="Francesca De Angeli, Paolo Montegriffo, Lovro Palaversa, Daniela Ruz-Mieres",
    author_email="fda@ast.cam.ac.uk",
    maintainer="Daniela Ruz-Mieres",
    maintainer_email="d.ruzmieres@ast.cam.ac.uk",
    description="Utilities to handle BP/RP (XP) Gaia low-resolution spectra as delivered via the archive",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gaia-dpci.github.io/GaiaXPy-website/",
    python_requires='>=3.6',
    packages=find_packages(),
    install_requires=required_packages,
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
    ]
)
