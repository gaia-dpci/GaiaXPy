Installation
============

---------
From PyPI
---------

GaiaXPy is available through PyPI. Use a Python version supported by the release you are installing; pip checks the declared Python requirement.

The PyPI command installs the public release. For development or pre-release functionality, use the source checkout supplied for that version.

To install the package, first ensure that the version of pip you are using is the one associated with Python 3 on your machine.

You can check this by running:

.. role:: bash(code)
   :language: bash

.. code-block:: sh

    python -m pip --version

Use ``python3`` instead of ``python`` if that is the command for your chosen Python installation. The output identifies the Python version associated with pip.

To install GaiaXPy from PyPI, simply run:

.. role:: bash(code)
   :language: bash

.. code-block:: sh

    pip install GaiaXPy

Or optionally:

.. code-block:: sh

    python -m pip install GaiaXPy

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
    python -m pip install .
    # For an editable development installation, use this instead:
    python -m pip install -e .
