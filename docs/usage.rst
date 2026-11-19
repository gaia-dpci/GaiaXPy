Usage
=====

.. note::
    This page contains a summary of how GaiaXPy should be used. For details, please consult the available `tutorials <https://gaia-dpci.github.io/GaiaXPy-website/tutorials.html>`_.

GaiaXPy provides tools for working with Gaia DR3 BP/RP mean spectra, including calibration, conversion to sampled spectra, synthetic photometry and plotting.

Supporting functions include covariance calculations, Cholesky factorisation, wavelength and pseudo-wavelength conversion.

This page introduces common inputs and outputs for the mean-spectrum tools.
See :doc:`gaiaxpy` for the full API reference.

.. role:: python(code)
   :language: python

------------------
Input data types
------------------

.. note::
    The following information does not apply to the :ref:`plotter <plotter>` functionality.

The mean-spectrum tools accept files, source-ID selections (lists or tuples of integers or integer strings), ADQL queries and `pandas <https://pandas.pydata.org/>`_ DataFrames, as described below.

Files
-----
Supported file formats are ``CSV``, ``ECSV``, ``FITS`` and ``XML/VOTable``. GaiaXPy accepts ``.csv.gz``, ``.ecsv.gz``, ``.fits.gz``, ``.xml.gz``, and
``.zip`` input files as downloaded from the `Gaia Archive <https://archives.esac.esa.int/gaia/>`_ directly. These use the same parsing, column selection, normalisation
and release validation as uncompressed inputs. Gzip-compressed output is not supported.

The mean-spectrum tools read continuous XP data from the `Gaia Archive <https://archives.esac.esa.int/gaia/>`_. Files must contain the columns required by the selected operation.

Source-ID lists and tuples
--------------------------
The :python:`calibrate`, :python:`convert` and :python:`generate` functions accept lists
or tuples of source IDs supplied as integers, integer strings, or a mixture. String IDs are converted to integers before Archive retrieval.

These functions retrieve the required DR3 data for the selected sources from the Gaia Archive.

Cosmos credentials can be supplied using :python:`username` and :python:`password`, or :python:`credentials_file`. Authentication may be requested when needed.

ADQL queries
------------
The same functions accept ADQL queries supplied as strings. Queries must return a source-ID column, for example:

.. code-block:: python

    query = "SELECT TOP 100 source_id FROM gaiadr3.gaia_source WHERE has_xp_continuous = 'True'"

This example selects sources with continuous XP spectra.

Cosmos credentials can be supplied using :python:`username` and :python:`password`, or :python:`credentials_file`. Authentication may be requested when needed.

DataFrames
----------
DataFrames must contain the columns and array values required by the selected operation. Use ``get_required_columns`` to inspect these requirements; see :doc:`faqs`.

Some tools require to have the columns :python:`bp_coefficient_correlations` and :python:`rp_coefficient_correlations`. The data in these two columns will be converted to matrices using the
function :python:`array_to_symmetric_matrix` if they come as arrays as it happens for the data served from the archive. No changes will be made if the data in these columns already correspond to matrices.

-------------
Generic usage
-------------

This section shows how to pass different types of input to a generic function in the package, which represents any of the available functions (:python:`calibrate`, :python:`convert`, etc.), and some considerations on output and storage.

.. note::
  In the following code snippet :python:`generic_function` should be replaced by the name of the function you wish to invoke (:python:`calibrate`, :python:`convert`, etc.).

Input
-----

.. code-block:: python

   from gaiaxpy import generic_function

   # Passing a file
   input_file = 'path/to/input/file.extension'
   output_data = generic_function(input_file)

   # Passing a DataFrame
   import pandas as pd
   input_file = 'path/to/input/file.extension'
   read_df = pd.read_csv(input_file, float_precision='round_trip')
   # The data can be modified as far as the names of the columns and the types remain the same.
   output_data = generic_function(read_df)

   # Passing a list
   sources = [1234567890123456789, "2345678901234567890"]
   output_data = generic_function(sources, release="dr3")

Output
------

Depending on the function being executed, the output can be just one variable for the data; or two, one for the data and another one for the sampling.

.. code-block:: python

   from gaiaxpy import generic_function

   input_file = 'path/to/input/file.extension'

   # Returning one output variable
   output_data = generic_function(input_file)

   # Returning two variables if it corresponds
   output_data, sampling = generic_function(input_file)

Storage
-------

The functions have the option :python:`save_file` which is set to :python:`True` by default.

The output file has the same extension as the input file unless the user chooses a different output format. In the case of elements that do not have an extension like lists and DataFrames, :python:`csv` is used by default.
The option :python:`output_format` selects ``CSV``, ``ECSV``, ``FITS`` or ``XML/VOTable``.

For calibrated and converted sampled spectra, ``CSV`` writes a data file and a separate ``<output_file>_sampling.csv`` file. CSV outputs also save provenance in ``<output_file>_metadata.csv``. Photometry tables do not have a separate sampling file.

``ECSV``, ``FITS``, ``XML/VOTable`` embed metadata and, for sampled-spectrum output, the sampling in the main file. Sampled-spectrum Avro output uses a separate ``_sampling.avro`` file.

.. code-block:: python

    from gaiaxpy import generic_function

    input_file = 'path/to/input/file.extension'
    output_data = generic_function(input_file, output_path='my/path', output_file='my_output_name', output_format='fits')

If the function accepts a sampling, it has to correspond to a NumPy array and be passed through the option :python:`sampling`.

.. code-block:: python

    import numpy as np
    from gaiaxpy import calibrate

    input_file = 'path/to/mean_spectrum.csv'
    output_data, output_sampling = calibrate(input_file, sampling=np.arange(336, 1021, 2))

.. warning::
    If an output file with the same name as an existing one is created,
    the data of the previous file will be automatically overwritten.

Output metadata
---------------

Calibration, conversion and photometry results store provenance and
relevant paper references in ``data.attrs['gaiaxpy_metadata']``. To read
it from a saved output, use:

.. code-block:: python

    from gaiaxpy.output import read_output_metadata

    metadata = read_output_metadata('output_spectra.csv')

The metadata also contains the paths to the configuration files used to compute
the output data.

For ``CSV``, the helper reads the companion ``_metadata.csv`` file. It also accepts
that companion's path directly.

Interaction with TOPCAT
-----------------------

`TOPCAT <http://www.star.bris.ac.uk/~mbt/topcat/>`_ can read the ``FITS`` and ``XML`` output files of the calibrator, converter, and generator. It is possible to plot their contents using TOPCAT.

The functionality that allows to generate these plots is the `XYArray Layer Control <http://www.star.bristol.ac.uk/~mbt/topcat/sun253/GangLayerControl_xyarray.html>`_.

A tutorial on how to work with TOPCAT is available `here <https://gaia-dpci.github.io/GaiaXPy-website/tutorials/TOPCAT%20tutorial.html>`_.

----------
Calibrator
----------

:python:`calibrate` returns a DataFrame of calibrated spectra and a NumPy array
of wavelengths in nm. The default sampling covers 336–1020 nm in 2 nm steps.
Custom wavelength grids must lie within [330, 1050] nm.

The default output file name is ``output_spectra``; use ``output_file`` to
choose another name. See :ref:`calibrate <calibrate>` for all parameters and
return values.

---------
Converter
---------

:python:`convert` returns a DataFrame of sampled BP/RP spectra and a NumPy
array of pseudo-wavelengths. The default sampling is
``numpy.linspace(0, 60, 600)``. Custom grids must lie within [0, 60].

See :ref:`convert <convert>` for all parameters and return values.

------------------------------
Synthetic photometry generator
------------------------------

:python:`generate` returns a DataFrame containing magnitudes, fluxes and flux
errors for each selected passband. Fluxes are in ``W nm^-1 m^-2`` for VEGAMAG
systems and ``W Hz^-1 m^-2`` for AB systems.

Choose photometric systems matching the input release, such as
``PhotometricSystem.DR3_JKC`` for DR3.
Use ``PhotometricSystem.get_available_systems()`` to list the available systems.
See :ref:`generate <generate>` for all parameters and return values.

For worked examples of calibration, conversion and synthetic photometry, see
the `GaiaXPy tutorials <https://gaia-dpci.github.io/GaiaXPy-website/tutorials.html>`_.

Photometric systems requests
----------------------------
Users can request the addition of other photometric systems by raising an `issue via GitHub <https://github.com/gaia-dpci/GaiaXPy/issues>`_.
The main conditions for adding a new system are the following:

* Only passbands that are fully enclosed in the Gaia BP/RP wavelength range ``[330, 1050] nm`` can be reproduced.
* Requests need to be properly justified. An example: it would be pointless to include a specific set of passbands that is used at a given telescope to approximate the JKC or SDSS systems. Synthetic magnitudes/fluxes (standardised or non-standardised) in these systems can be already obtained with GaiaXPy. On the other hand, it would be useful to include a set of passbands adopted by an existing or forthcoming survey that intends to provide magnitudes in its own “natural” photometric system, or a set aimed at tracing a specific feature/characteristic of the available XP spectra, not covered by already included passbands.
* The newly added systems will be publicly available to all GaiaXPy users.
* The new system to be added is specified as follows:

  * one ``CSV`` file per passband, containing the following columns: wavelength in nm or Angstrom, total response in arbitrary units.
  * it must be clearly specified if the transmission curves are photonic curves or energy curves (see, e.g., ``Bessell & Murphy 2012``).
  * it must be clearly specified if the desired magnitudes are ``VEGAMAG`` or ``AB`` mag.
  * a reference for the source of all the above info (especially the transmission curves) must be provided.

All the available options for this method can be found in :ref:`generate <generate>`.

Additional photometric systems
------------------------------
The Spanish Virtual Observatory (`SVO <https://svo.cab.inta-csic.es/main/index.php>`_)
provides additional photometric-system files for Gaia DR3. These XML files can
be downloaded and loaded into GaiaXPy (version ``2.0.0`` or later) to generate synthetic photometry alongside
the built-in systems.

These files contain additional photometric systems from which synthetic photometry can be generated in the same way it is done with the built-in GaiaXPy systems.

A tutorial on how to use this functionality is available in the `Tutorials section <https://gaia-dpci.github.io/GaiaXPy-website/tutorials.html>`_ of the main GaiaXPy webpage.

``PhotometricSystem`` is a stable registry of the currently available systems.
To load additional systems:

.. code-block:: python

    from gaiaxpy import PhotometricSystem, load_additional_systems, remove_additional_systems

    load_additional_systems('/path/to/filters')
    system = PhotometricSystem.USER_DR3_Sdss_v1
    names = PhotometricSystem.get_available_systems()
    remove_additional_systems()

The argument can be a single filter file or a directory, supplied as ``str`` or
``pathlib.Path``. Directory discovery is recursive. Selecting a file loads only
that file. Supported filenames are ``<system>.gaiaxpy_dr3_<version>.xml``, case-insensitively.

Downloaded DR3 XML files and user-created files following this convention
remain usable without modifications to their contents. Directory discovery warns
with paths for unrelated files that it ignores. Explicitly selecting an unsupported
filename, or a filter declaring an unsupported release/format combination, raises
an error. A directory containing a recognisable but unsupported release/format
combination also raises an error.

Additional systems are identified by release, base system name and version.
Different systems may use different versions, and multiple versions of one system
can be loaded together. For example, these files may coexist:

.. code-block:: text

    Example.gaiaxpy_dr3_v1.xml
    Example.gaiaxpy_dr3_v2.xml
    Other.gaiaxpy_dr3_v7.xml

Select each version explicitly:

.. code-block:: python

    from gaiaxpy import generate

    load_additional_systems('/path/to/filters')
    systems = [PhotometricSystem.USER_DR3_Example_v1,
               PhotometricSystem.USER_DR3_Example_v2]
    photometry = generate(input_data, photometric_system=systems, save_file=False)

Additional-system identifiers and photometry column labels always include the
version, even when only one version is loaded. There are no unversioned aliases. For a band ``G``, the example
produces distinct columns such as ``USER_DR3_Example_v1_flux_G`` and
``USER_DR3_Example_v2_flux_G``. Use ``get_available_systems()`` to see the
filter names.

References imported by other modules see the same updated selection. Existing
code such as ``PhotometricSystem = load_additional_systems(path)`` continues to
work. Subsequent loads replace the additional selection after confirmation;
they do not accumulate systems. A failed load leaves the previous selection and
configuration unchanged. Removing or replacing a selection invalidates its
previously selected additional-system objects.

Filter versions and optional metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``system.get_version()`` reports the version of the selected filter file. Built-in
filters use their embedded metadata; their versions are independent of the
GaiaXPy package version.

DR3 XML files without a metadata block remain supported.
Their versions come from their filenames, and ``get_metadata()`` returns an empty
dictionary. Conflicting or malformed metadata causes the complete load to fail
before replacing the previous selection.

For user-created files, the user assigns the version to identify their own
configuration as part of the file name; it does not imply an official Gaia
or SVO release.

.. _plotter:

-------
Plotter
-------

This functionality allows to plot the output of the calibrator and converter. It receives the output DataFrame and the output_sampling.

.. code-block:: python

    from gaiaxpy import plot_spectra
    plot_spectra(output_data, sampling=output_sampling, multi=False, show_plot=True, output_path='/path')

The parameter :python:`multi` set as :python:`True` plots all the results in the image, whereas :python:`False` generates one plot per spectrum in the data.
The parameter :python:`show_plot` shows the images if it is set as :python:`True`. If a :python:`output_path` is provided, the plots are automatically saved.

By default, plot labels do not require LaTeX. Set ``use_tex=True`` to render labels using LaTeX; this requires a LaTeX installation.

All the available options are described in :ref:`plot_spectra <plotter>`.
