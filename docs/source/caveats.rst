Caveats
=======

Plotter
-------

The output DataFrames contain metadata indicating which type of spectra they contain. The plotter tool relies
on this information to know which type of plot to generate. Pandas does not yet have a robust method of
propagating metadata attached to DataFrames, so if some operations are performed over the DataFrame, this information
may be lost. Luckily, most common operations preserve metadata.

Also, the plotter can only receive pandas DataFrames and not pandas Series.

Minimum requirements
--------------------

GaiaXPy works with Python 3.6 and later.

Regarding the operating system used, an installation issue has been reported when using a system older than macOS Monterey 12.1.
