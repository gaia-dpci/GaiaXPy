FAQs
====

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

GaiaXPy expects to receive a pandas DataFrame with at minimum the columns and types:

* ``source_id`` (``int``)
* ``bp_n_parameters`` (``int``)
* ``rp_n_parameters`` (``int``)
* ``bp_coefficients`` (NumPy ndarray)
* ``bp_coefficient_errors`` (NumPy ndarray)
* ``bp_coefficient_correlations`` (NumPy ndarray)
* ``rp_coefficients`` (NumPy ndarray)
* ``rp_coefficient_errors`` (NumPy ndarray)
* ``rp_coefficient_correlations`` (NumPy ndarray)
* ``bp_basis_function_id`` (``int``, only required if ``truncation=True``)
* ``rp_basis_function_id`` (``int``, only required if ``truncation=True``)

If strings are present in the data, the program will fail.

The NumPy ndarrays should be 1-dimensional arrays. In the case of ``bp_coefficient_correlations`` and ``rp_coefficient_correlations``, both 1-dimensional and 2-dimensional arrays are accepted. If a 1-dimensional array is passed, the program will use the function `array_to_symmetric_matrix <https://gaiaxpy.readthedocs.io/en/latest/gaiaxpy.core.html#gaiaxpy.core.generic_functions.array_to_symmetric_matrix>`_ to transform the array. If a 2-dimensional array is received, no changes will be applied. This 2-dimensional array should have dimensions ``(55, 55)``.
