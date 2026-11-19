FAQs
====

How can I ask a question or provide feedback?
---------------------------------------------

Please refer to the :doc:`support` section on the side navigation bar.

How can I request a photometric system to be added?
---------------------------------------------------

Users can request the addition of other photometric systems by raising an `issue via GitHub <https://github.com/gaia-dpci/GaiaXPy/issues>`_.
The main conditions for adding a new system are the following:

* Only passbands that are fully enclosed in the Gaia BP/RP wavelength range [330, 1050] nm can be reproduced.
* Requests need to be properly justified. An example: it would be pointless to include a specific set of passbands that is used at a given telescope to approximate the JKC or SDSS systems. Synthetic magnitudes/fluxes (standardised or non-standardised) in these systems can be already obtained with GaiaXPy. On the other hand, it would be useful to include a set of passbands adopted by an existing or forthcoming survey that intends to provide magnitudes in its own “natural” photometric system, or a set aimed at tracing a specific feature/characteristic of the available XP spectra, not covered by already included passbands.
* The newly added systems will be publicly available to all GaiaXPy users.
* The new system to be added is specified as follows:

  * one CSV file per passband, containing the following columns: wavelength in nm or Angstrom, total response in arbitrary units.
  * it must be clearly specified if the transmission curves are photonic curves or energy curves (see, e.g., Bessell & Murphy 2012).
  * it must be clearly specified if the desired magnitudes are VEGAMAG or AB mag.
  * a reference for the source of all the above info (especially the transmission curves) must be provided.


GaiaXPy can receive pandas DataFrames, what type of frame is it expecting?
-------------------------------------------------------------------------------

Required columns depend on the operation. Inspect them without loading data:

.. code-block:: python

    from gaiaxpy import get_required_columns

    requirements = get_required_columns("calibrate")
    print(requirements.required)
    print(requirements.conditional)

You can also pass the function itself to ``get_required_columns`` instead of just its name:

.. code-block:: python

    from gaiaxpy import calibrate, get_required_columns

    requirements = get_required_columns(calibrate)
    print(requirements.required)
    print(requirements.conditional)

For calibration, conversion and generation, use the Archive coefficient-column names and provide the required error information. When ``truncation=True``, the per-source ``bp_n_relevant_bases`` and ``rp_n_relevant_bases`` counts are required.

This will also be described in the tutorials. Access the tutorials `here <https://gaia-dpci.github.io/GaiaXPy-website/tutorials.html>`_.

Recognised array fields accept NumPy arrays and supported text representations. Coefficient correlations may be packed one-dimensional arrays or square matrices. Their dimensions must match that photometer's coefficient count.
