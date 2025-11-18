Installation
============

---------
From PyPI
---------

GaiaXPy was designed to work with Python 3.10 or later, and is available through PyPI. Previous versions of the
package are compatible with Python 3.6.

To install the package, first ensure that the version of pip you are using is the one associated with the version of
Python you want to use.

You can check this by running:

.. role:: bash(code)
   :language: bash

.. code-block:: sh

    pip --version

You should see a Python version at the end of the output of these commands. E.g.: :python:`python 3.10`.

To install GaiaXPy from PyPI, simply run:

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
    # Or, optionally, you can clone just a specific branch in the repo
    git clone --branch my-branch https://github.com/gaia-dpci/GaiaXPy
    # Navigate to the GaiaXPy directory
    cd GaiaXPy
    # Create a virtual environment
    python3 -m venv .env
    # Activate the environment
    source .env/bin/activate
    # Install the package
    pip install -e .
