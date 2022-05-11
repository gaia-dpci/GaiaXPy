Usage
=====

The package currently includes four different functionalities: a **calibrator**, a **converter**, a **synthetic photometry generator** and a **plotter**. A further functionality, a **simulator**, is under development and will be released soon.

.. role:: python(code)
   :language: python

------------------
Input data types
------------------

**Note:** The following information does not apply to the **plotter** functionality.

The functions in GaiaXPy can receive different kinds of inputs. The ones currently implemented are :python:`files`, :python:`lists` , :python:`ADQL queries` and `pandas <https://pandas.pydata.org/>`_ :python:`DataFrames`.

Files
-----
The functions accept input files with the extensions: :python:`avro`, :python:`csv`, :python:`fits`, and :python:`xml`.
All these, but :python:`avro`, are files that contain XP continuous raw data as extracted from the `Gaia archive <https://gea.esac.esa.int/archive/>`_.

Lists
-----
Lists are accepted only by the :python:`calibrator`, :python:`converter`, and :python:`generator`. These lists have to correspond to a list of source IDs. Both lists of strings and lists of long are accepted.

When a list is passed to one of the tools, the function will internally request the required data for the given sources from the Gaia Archive (currently geapre), ask for
credentials (username and password), execute the function, and return the results.

ADQL queries
------------
ADQL queries are accepted only by the :python:`calibrator`, :python:`converter`, and :python:`generator`. Queries need to be passed as strings (e.g.: :python:`"select TOP 100 source_id from user_dr3int6.gaia_source where has_xp_continuous = 'True'"`).

Queries are sent to the Gaia Archive (geapre), and executed after requesting credentials (username and password).

DataFrames
----------
DataFrames can be accepted by all the tools available and will work as far as the names of the columns in the DataFrame match the columns used in the files extracted from the Gaia Archive.

Some tools require to have the columns :python:`bp_coefficient_correlations` and :python:`rp_coefficient_correlations`. The data in these two columns will be converted to matrices using the
function :python:`array_to_symmetric_matrix` if they come as arrays as it happens for the data served from the archive. No changes will be made if the data in these columns already correspond to matrices.

-------------
Generic usage
-------------

This section shows how to pass different types of input to a generic function in the package that represents the actual tools and some considerations on output and storage.

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
   sources = [1234567890, 0987654321] # Or ['1234567890', '0987654321'] as strings
   output_data = generic_function(sources)

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
The option :python:`output_format` allows to store the data in the formats :python:`avro`, :python:`csv`, :python:`fits`, and :python:`xml`.

Depending on the format chosen to store the data, the functions will create one or two files. The formats :python:`fits` and :python:`xml` will create one file that contains both the data and the sampling.
However, the formats :python:`avro` and :python:`csv` will generate two files, one for each of the output variables. In this case, the name of the sampling file will include the suffix :python:`_sampling`.

.. code-block:: python

    from gaiaxpy import generic_function

    input_file = 'path/to/input/file.extension'
    output_data = generic_function(input_file, output_file='my_output_name', output_format='fits')

If the function accepts a sampling, it has to correspond to a NumPy array and be passed through the option :python:`sampling`.

.. code-block:: python

    import numpy as np
    from gaiaxpy import generic_function

    input_file = 'path/to/input/file.extension'
    output_data, output_sampling = generic_function(input_file, sampling=np.linspace(0, 100, 1000))

**IMPORTANT NOTE: If an output file with the same name as an existing one is created, the data of the previous file will be automatically overwritten.**

Note on TOPCAT
--------------

`TOPCAT <http://www.star.bris.ac.uk/~mbt/topcat/>`_ can read the FITS and XML output files of the calibrator and converter. It is possible to plot the contents of the XML using TOPCAT.

The functionality that allows to generate these plots is the `XYArray Layer Control <http://www.star.bristol.ac.uk/~mbt/topcat/sun253/GangLayerControl_xyarray.html>`_. A short tutorial on how to use this functionality will be available in the future.

----------
Calibrator
----------

The function :python:`calibrate` returns a DataFrame of calibrated spectra and a NumPy array with the sampling. The default output file name is :python:`'output_spectra'`, but the user can choose a different one.

.. code-block:: python

   import numpy
   from gaiaxpy import calibrate

   mean_spectrum_file = 'path/to/mean_spectrum_with_correlation.csv'
   calibrated_df, sampling = calibrate(mean_spectrum_file, sampling=numpy.linspace(0, 60, 600), save_file=False)

The default sampling is :python:`numpy.linspace(0, 60, 600)`; however, in order to improve the resolution at the blue end, the log-scale sampling :python:`numpy.geomspace(330, 1049.9999999999, 361)` is proposed as an alternative.

All the available options can be found in :ref:`calibrate <calibrate>`.

---------
Converter
---------

The function :python:`convert` returns a DataFrame where each row corresponds to a converted spectrum, and a NumPy array with the sampling.

.. code-block:: python

    from gaiaxpy import convert

    mean_spectrum_file = 'path/to/mean_spectrum_with_correlation.csv'
    converted_data, sampling = convert(mean_spectrum_file, save_file=False)

There is also a default sampling which is :python:`numpy.linspace(0, 60, 600)`.

.. code-block:: python

    from gaiaxpy import convert

    mean_spectrum_file = 'path/to/mean_spectrum_with_correlation.csv'
    converted_data, sampling = convert(mean_spectrum_file, sampling=numpy.linspace(0, 100, 1000), output_file='my_output_name', output_format='.xml')

All the available options can be found in :ref:`convert <convert>`.

------------------------------
Synthetic photometry generator
------------------------------

The synthetic photometry utility uses the method :python:`generate` to return a DataFrame with the generated synthetic photometry results.
Magnitudes, fluxes and flux errors are computed for each filter. The synthetic fluxes are given in units
of W nm :superscript:`-1` m :superscript:`-2`.

.. code-block:: python

    from gaiaxpy import generate, PhotometricSystem

    mean_spectrum_file = 'path/to/mean_spectrum_with_correlation.csv'
    phot_system = PhotometricSystem.JOHNSON
    generated_data = generate(mean_spectrum_file, phot_system, save_file=False)

The available systems are updated as requested. Gaia DR3, Johnson-Kron-Cousins, SDSS, HST WFC3/UVIS are some of the ones currently available.
For a complete list use

.. code-block:: python

    from gaiaxpy import PhotometricSystem

    PhotometricSystem.get_available_systems()

All the available options for this method can be found in :ref:`generate <generate>`.

-------
Plotter
-------

This functionality allows to plot the output of the calibrator and converter. It receives the output DataFrame and the output_sampling.

.. code-block:: python

    from gaiaxpy import plot_spectra
    plot_spectra(output_data, sampling=output_sampling, multi=False, show_plot=True, output_path='/path')

The parameter :python:`multi` set as :python:`True` plots all the results in the image, whereas :python:`False` generates one plot per spectrum in the data.
The parameter :python:`show_plot` shows the images if it is set as :python:`True`. If a :python:`output_path` is provided, the plots are automatically saved.

All the available options are described in :ref:`plotter <plotter>`.
