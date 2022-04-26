Installation
============

GaiaXPy is not currently available through a package manager, and therefore needs to be manually installed.

To install GaiaXPy, Python3 is required, and it is recommended to create a virtual environment first:

.. role:: bash(code)
   :language: bash

.. code-block:: sh

    # Move to the package directory
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
