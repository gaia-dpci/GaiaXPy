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

GaiaXPy works with Python 3.7 and later on Linux, MacOS, and Windows. If a problem is found, it is recommended to report
it by creating a `GitHub issue <https://github.com/gaia-dpci/GaiaXPy/issues>`_.

Previous versions of GaiaXPy were compatible with Python 3.6.

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
The problem can be resolved by installing urllib3 version 1.26.6:

.. code-block:: python

    pip install urllib3==1.26.6

More information `here <https://github.com/urllib3/urllib3/issues/3020>`_.
