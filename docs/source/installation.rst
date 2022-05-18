Installation
============

---------
From PyPI
---------

GaiaXPy was designed to work with Python 3.6 or later, and is available through PyPI.

To install the package, first ensure that the version of pip you are using
is the one associated with Python 3 in your machine.

You can check this by running:

.. role:: bash(code)
   :language: bash

.. code-block:: sh

    pip --version

Or:

.. role:: bash(code)
   :language: bash

.. code-block:: sh

    pip3 --version

You should see a Python version at the end of the output of these commands. E.g.: :python:`python 3.8`.

To install GaiaXPy from PyPI, simply run:

.. role:: bash(code)
   :language: bash

.. code-block:: sh

    pip install GaiaXPy # or pip3 if it corresponds

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
    # Install the package
    python setup.py install
