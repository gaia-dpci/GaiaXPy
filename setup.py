"""
Setup module for GaiaXPy.

Francesca De Angeli, Paolo Montegriffo, Lovro Palaversa, Daniela Ruz-Mieres - 2022

Based on:
https://packaging.python.org/tutorials/packaging-projects
"""

import sys
from os import path
from setuptools import setup, find_packages

current_path = path.abspath(path.dirname(__file__))
README = open(path.join(current_path, "README-pypi.rst")).read()
NEWS = open(path.join(current_path, "NEWS.txt")).read()

with open("requirements.txt") as f:
    required_packages = f.readlines()

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="GaiaXPy",
    version="0.1.0",
    author="Francesca De Angeli, Paolo Montegriffo, Lovro Palaversa, Daniela Ruz-Mieres",
    author_email="fda@ast.cam.ac.uk",
    maintainer="Daniela Ruz-Mieres",
    maintainer_email="d.ruzmieres@ast.cam.ac.uk",
    description="Utilities to handle BP/RP (XP) Gaia low-resolution spectra as delivered via the archive",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://gitlab.com/pyxp-developers",
    python_requires='>=3.6',
    packages=find_packages(),
    install_requires=required_packages,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD 3-Clause License",
        "Operating System :: OS Independent",
    ]
)
