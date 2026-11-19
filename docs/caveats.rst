Caveats / Known issues
======================

.. role:: python(code)
   :language: python

Plotter
-------

The output DataFrames contain metadata indicating which type of spectra they contain. This metadata can be accessed
through the attribute :python:`attrs`. The plotter tool relies on this information to know which type of plot to generate.

Pandas does not yet have a robust method of propagating metadata attached to DataFrames. As a result, if certain
operations are applied to the DataFrame, this information may be lost which will cause the plotter to fail. Luckily,
most common operations preserve metadata.

Minimum requirements
--------------------

Use a Python version supported by the GaiaXPy release you are installing; see :doc:`installation`. For questions and bug reports, see :doc:`support`.

Filters
-------

Since GaiaXPy was originally published, two issues with photometric filters have been found. The affected filters are
**SDSS** and **PanSTARRS1_Std**.

**SDSS**: The SDSS filters (available as PhotometricSystem.SDSS) that were originally published have been replaced with
those defined in `Doi et al. 2010, AJ, 141, 47 <https://ui.adsabs.harvard.edu/abs/2010AJ....139.1628D/abstract>`_.
Note that the standardised version (PhotometricSystem.SDSS_Std) was already based on Doi et al. 2010, AJ, 141, 47 and is
therefore unchanged with respect to previous versions of GaiaXPy.

**PanSTARRS1_Std**: Due to a bug in GaiaXPy, the synthetic photometry for the standardised PanSTARRS1 y band (contained
in the fields y_ps1_flux, y_ps1_flux_error and y_ps1_mag) has been generated without applying the flux offset mitigating
the systematic effect at the faint end due to background issues (also referred to as hockey-stick, see Section 2.2.1 and
equation 13 in `Gaia Collaboration, Montegriffo, et al., 2022 <https://ui.adsabs.harvard.edu/abs/2022arXiv220606215G/abstract>`_).
The offset should have been applied to the synthetic flux and then propagated to the flux error and magnitude. However,
no offset was being applied.

Both issues were **fixed in GaiaXPy version 1.2.4**.

OpenSSL / LibreSSL
------------------
In some cases, an incompatibility problem with OpenSSL/LibreSSL may arise. This is due to a problem with recent versions
of the urllib3 (as of May 2023) used by the requests library which is required to connect to the Gaia Archive.
The error message contains the sentence: "urllib3 v2.0 only supports OpenSSL 1.1.1+"
For this historical incompatibility, see the `upstream report <https://github.com/urllib3/urllib3/issues/3020>`_. Follow the compatibility guidance for your installed urllib3 version rather than automatically pinning an older release. Include the full error and environment versions when asking for help; see :doc:`support`.


Ubuntu 22.04 (plotting)
-----------------------
On ``Ubuntu 22.04 LTS`` with GaiaXPy version ``2.1.3`` onwards, some small plotting-related errors may occur
due to missing LaTeX-related system dependencies. These are not issues with GaiaXPy itself, but with the local environment.

The following error may appear when producing plots:

.. code-block:: bash

    ! LaTeX Error: File `type1ec.sty` not found.

This can be resolved by installing the ``CM-Super`` fonts:

.. code-block:: bash

    sudo apt-get -y install cm-super

After this, the following error may occur:

.. code-block:: bash

    Failed to process string with tex because dvipng could not be found.

This can be fixed by installing ``dvipng``:

.. code-block:: bash

    sudo apt-get install dvipng

CentOS 7 (installation)
-----------------------
On systems running ``CentOS 7`` (which reached end of life in June 2024), GaiaXPy version ``2.1.3`` and later cannot
be installed.

This is due to the system compiler (``gcc 4.8``) lacking support for ``stdatomic.h``, which was introduced in ``gcc 4.9``.
As a result, building GaiaXPy fails on these systems.

Support for ``stdatomic.h`` was added in ``gcc 4.9``: `see details <https://gcc.gnu.org/gcc-4.9/changes.html>`_.