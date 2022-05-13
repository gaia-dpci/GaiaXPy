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
    https://github.com/gaia-dpci/GaiaXPy
    # Create a virtual environment
    python3 -m venv .env
    # Activate the environment
    source .env/bin/activate
    # Install package requirements
    pip install -r requirements.txt
    # Install the GaiaXPy package in editable mode
    pip install -e .


Installation
============

GaiaXPy works with Python 3 and is **not** available through a package manager yet, but is expected to be available through PyPI in the near future.

To install GaiaXPy simply run:

.. role:: bash(code)
   :language: bash

.. code-block:: sh

    cd GaiaXPy
    # Create a virtual environment
    python3 -m venv .env
    # Activate the environment
    source .env/bin/activate
    # Install package requirements
    pip install -r requirements.txt
    # Install the GaiaXPy package in interactive mode
    pip install -e .

To test the installation (with the virtual environment activated):

.. code-block:: sh

    # Check the python version, it needs to be 3.x
    python --version
    # Open a Python console, just typing one of the following:
    python, python3, or ipython3
    # Import the package (you should get no errors)
    import gaiaxpy

If the previous steps succeed, then GaiaXPy is correctly installed.
