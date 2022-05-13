Installation
============

GaiaXPy works with Python 3 and is **not** available through a package manager yet, but is expected to be available through PyPI in the near future.

---------
From PyPI
---------

To install GaiaXPy from PyPI, once it's available, simply run:

.. role:: bash(code)
   :language: bash

.. code-block:: sh

    pip install GaiaXPy

-----------
From source
-----------

To install GaiaXPy from source:

.. role:: bash(code)
   :language: bash

.. code-block:: sh

    # Clone the repository
    git clone https://github.com/gaia-dpci/GaiaXPy
    # Navigate to the GaiaXPy directory
    cd GaiaXPy
    # Create a virtual environment
    python3 -m venv .env
    # Activate the environment
    source .env/bin/activate
    # Install package requirements
    pip install -r requirements.txt
    # Install the GaiaXPy package in editable mode
    pip install -e .
