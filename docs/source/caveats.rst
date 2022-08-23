Caveats / Known issues
======================

.. role:: python(code)
   :language: python

Plotter
-------

The output DataFrames contain metadata indicating which type of spectra they contain. This metadata
can be accessed through the attribute :python:`attrs`. The plotter tool relies on this information
to know which type of plot to generate.

Pandas does not yet have a robust method of propagating metadata attached to DataFrames,
so if some operations are performed over the DataFrame, this information may be lost.
Luckily, most common operations preserve metadata.

The plotter can only receive pandas DataFrames and not pandas Series, which may be important when
selecting a particular row of a DataFrame.

For example, if :python:`df` is a DataFrame returned by GaiaXPy corresponding to either the calibrator or converter output,
and we want to select row :python:`0` and the use :python:`plot_spectra` on it:

.. code-block:: python

    df.iloc[0] # Will return a Pandas Series, not accepted by plot_spectra
    df.iloc[[0]] # Will return a Pandas DataFrame, accepted by plot_spectra

Minimum requirements
--------------------

GaiaXPy works with Python 3.6 and later.

Regarding the operating system, an installation issue has been reported when using a system older than macOS Monterey 12.1. Other details about this issue are unclear, but if a problem is found, it is recommend it to report it by creating an `GitHub issue <https://github.com/gaia-dpci/GaiaXPy/issues>`_.

So far, no problems have been reported with other operating systems.
