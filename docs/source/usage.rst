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
The functions accept input files with the extensions: :python:`csv`, :python:`ecsv`, :python:`fits`, and :python:`xml`.
These are files that contain XP continuous raw data as extracted from the `Gaia archive <https://archives.esac.esa.int/gaia/>`_.

Lists
-----
Lists are accepted only by :python:`calibrate`, :python:`convert`, and :python:`generate`. These lists have to correspond to a list of source IDs. Both lists of strings and lists of long are accepted.

When a list is passed to one of the tools, the function will internally request the required data for the given sources from the Gaia archive.

Passing Cosmos credentials (username and password) is optional.

ADQL queries
------------
ADQL queries are accepted only by the :python:`calibrate`, :python:`convert`, and :python:`generate`. Queries need to be passed as strings (e.g.: :python:`"select TOP 100 source_id from gaiadr3.gaia_source where has_xp_continuous = 'True'"`).

Cosmos credentials (username and password) are optional.

DataFrames
----------
DataFrames can be accepted by all the tools available and will work as far as the names of the columns in the DataFrame match the columns used in the files extracted from the Gaia Archive.

Some tools require to have the columns :python:`bp_coefficient_correlations` and :python:`rp_coefficient_correlations`. The data in these two columns will be converted to matrices using the
function :python:`array_to_symmetric_matrix` if they come as arrays as it happens for the data served from the archive. No changes will be made if the data in these columns already correspond to matrices.

-------------
Generic usage
-------------

This section shows how to pass different types of input to a generic function in the package (which could be :python:`calibrate`, :python:`convert`, etc.) and some considerations on output and storage.

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
The option :python:`output_format` allows to store the data in the formats :python:`avro`, :python:`csv`, :python:`ecsv`, :python:`fits`, and :python:`xml`.

Depending on the format chosen to store the data, the functions will create one or two files. The formats :python:`fits` and :python:`xml` will create one file that contains both the data and the sampling.
However, the formats :python:`avro` and :python:`csv` will generate two files, one for each of the output variables. In this case, the name of the sampling file will include the suffix :python:`_sampling`.

.. code-block:: python

    from gaiaxpy import generic_function

    input_file = 'path/to/input/file.extension'
    output_data = generic_function(input_file, output_path='my/path', output_file='my_output_name', output_format='fits')

If the function accepts a sampling, it has to correspond to a NumPy array and be passed through the option :python:`sampling`.

.. code-block:: python

    import numpy as np
    from gaiaxpy import generic_function

    input_file = 'path/to/input/file.extension'
    output_data, output_sampling = generic_function(input_file, sampling=np.linspace(0, 100, 1000))

**IMPORTANT NOTE: If an output file with the same name as an existing one is created, the data of the previous file will be automatically overwritten.**

Note on TOPCAT
--------------

`TOPCAT <http://www.star.bris.ac.uk/~mbt/topcat/>`_ can read the FITS and XML output files of the calibrator and converter. It is possible to plot their contents using TOPCAT.

The functionality that allows to generate these plots is the `XYArray Layer Control <http://www.star.bristol.ac.uk/~mbt/topcat/sun253/GangLayerControl_xyarray.html>`_.

A tutorial on how to work with TOPCAT is available `here <https://gaia-dpci.github.io/GaiaXPy-website/tutorials/TOPCAT%20tutorial.html>`_.

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
    converted_data, sampling = convert(mean_spectrum_file, sampling=numpy.linspace(0, 70, 1000), output_file='my_output_name', output_format='.xml')

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
    phot_system = PhotometricSystem.JKC
    generated_data = generate(mean_spectrum_file, phot_system, save_file=False)

The following table lists the available systems providing references for the passband definitions.
The last column indicate the presence of a standardised version of the same set of filters (see
Gaia Collaboration, Montegriffo et al. 2022 for details). The asterisk for the HST WFC3 UVIS and
ACS WFC systems indicates that only a small selection (f438w, f606w, f814w) of the bands in these
two systems have been standardised using the HUGS catalogue (Nardiello, D., et al. 2018, The Hubble Space Telescope UV Legacy Survey of Galactic Globular
Clusters - XVII. Public Catalogue Release, 481, 3382–3393). These are available as HST_HUGS in GaiaXPy.
No ultraviolet band is provided in the standardised version of the Stromgren system (this is also indicated
with an asterisk in the table below).

.. role::  raw-html(raw)
    :format: html
.. list-table::
   :widths: 20, 20, 20, 30, 10
   :header-rows: 1
   :class: tight-table

   * - GaiaXPy
     - Name
     - Passbands
     - Reference
     - Standardised
   * - DECam
     - DECam
     - g, r, i, z, Y
     - https://noirlab.edu/science/programs/ctio/filters/Dark-Energy-Camera
     -
   * - Els_Custom_W09_S2
     - Custom
     - Halpha, Hbeta, O3, CHalpha, CHbeta, CO3, r, i
     - Gaia Collaboration, Montegriffo et al. 2022
     -
   * - Euclid_VIS
     - Euclid VIS
     - VIS
     - http://svo2.cab.inta-csic.es/svo/theory/fps3 (Euclid/VIS)
     -
   * - Gaia_2
     - Gaia 2
     - C1B431, C1B556, C1B655, C1B768, C1B916, C1M326, C1M344, C1M379, C1M395, C1M410, C1M467, C1M506, C1M515, C1M549, C1M656, C1M716, C1M747, C1M825, C1M861, C1M965
     - Jordi et al. 2006, MNRAS, 367, 290–314
     -
   * - Gaia_DR3_Vega
     - Gaia DR3
     - G, BP, RP
     - https://www.cosmos.esa.int/web/gaia/edr3-passbands
     -
   * - Halpha_Custom_AB
     - Custom
     - Halpha01nm, Halpha02nm, Halpha03nm, Halpha04nm, Halpha05nm, Halpha06nm, Halpha07nm, Halpha08nm, Halpha09nm, Halpha10nm
     - Gaia Collaboration, Montegriffo et al. 2022
     -
   * - H_custom
     - Custom
     - Hbeta_1.0, Hbeta_2.0, Hbeta_3.0, Hbeta_4.0, Hbeta_5.0, Hbeta_6.0, Hbeta_7.0, Hbeta_8.0, Hbeta_9.0, Hbeta_10.0, Hbeta_11.0, Hbeta_12.0, Hbeta_13.0, Hbeta_14.0, Hbeta_15.0, Hbeta_16.0, Hbeta_17.0, Hbeta_18.0, Hbeta_19.0, Hbeta_20.0, Hbeta_21.0, Hbeta_22.0, Hbeta_23.0, Hbeta_24.0, Hbeta_25.0, Halpha_1.0, Halpha_2.0, Halpha_3.0, Halpha_4.0, Halpha_5.0, Halpha_6.0, Halpha_7.0, Halpha_8.0, Halpha_9.0, Halpha_10.0, Halpha_11.0, Halpha_12.0, Halpha_13.0, Halpha_14.0, Halpha_15.0, Halpha_16.0, Halpha_17.0, Halpha_18.0, Halpha_19.0, Halpha_20.0, Halpha_21.0, Halpha_22.0, Halpha_23.0, Halpha_24.0, Halpha_25.0
     - Gaia Collaboration, Montegriffo et al. 2022
     -
   * - Hipparcos_Tycho
     - Hipparcos/Tycho
     - Hp, BT, VT
     - Bessell, M. & Murphy, S. 2012, PASP, 124, 140
     -
   * - HST_ACSWFC
     - HST ACSWFC
     - f435w, f475w, f550m, f555w, f606w, f625w, f775w, f814w, f850lp
     - http://svo2.cab.inta-csic.es/svo/theory/fps3 (HST/ACS_WFC)
     - :raw-html:`&check;` :raw-html:`&ast;`
   * - HST_WFC3UVIS
     - HST WFC3UVIS
     - f336w, f343n, f350lp, f390m, f390w, f395n, f410m, f438w, f467m, f475w, f475x, f547m, f555w, f600lp, f606w, f621m, f625w, f657n, f665n, f673n, f680n, f689m, f763m, f775w, f814w, f845m, f850lz, f373n, f469n, f487n, f502n, f631n, f645n, f656n, f658n
     - http://svo2.cab.inta-csic.es/svo/theory/fps3 (HST/WFC3_UVIS1)
     - :raw-html:`&check;` :raw-html:`&ast;`
   * - HST_WFPC2
     - HST WFPC2
     - f300w, f336w, f380w, f410m, f439w, f450w, f467m, f547m, f555w, f569w, f606w, f622w, f675w, f702w, f785lp, f791w, f814w, f850lp
     - http://svo2.cab.inta-csic.es/svo/theory/fps3 (HST/WFPC2-WF)
     -
   * - IPHAS
     - IPHAS
     - Halpha, r, i
     - Barentsen et al. 2014, MNRAS, 444, 3230
     -
   * - JKC
     - Johnson-Kron-Cousins
     - U, B, V, R, I
     - Bessell,M. & Murphy,S. 2012, PASP, 124, 140B
     - :raw-html:`&check;`
   * - JPAS
     - JPAS
     - uJava, u, J0378, J0390, J0400, J0410, J0420, J0430, J0440, J0450, J0460, J0470, J0480, gSDSS, J0490, J0500, J0510, J0520, J0530, J0540, J0550, J0560, J0570, J0580, J0590, J0600, J0610, J0620, rSDSS, J0630, J0640, J0650, J0660, J0670, J0680, J0690, J0700, J0710, J0720, J0730, J0740, J0750, J0760, iSDSS, J0770, J0780, J0790, J0800, J0810, J0820, J0830, J0840, J0850, J0860, J0870, J0880, J0890, J0900, J0910, J1007
     - Benitez et al. 2014, J-PAS Red Book, arXiv:1403.5237
     -
   * - JPLUS
     - JPLUS
     - uJAVA, J0378, J0395, J0410, J0430, gJPLUS, J0515, rJPLUS, J0660, iJPLUS, J0861, zJPLUS
     - Cenarro et al. 2019 A&A, 622, 176
     -
   * - JWST_NIRCAM
     - JWST NIRCam
     - F070W, F090W
     - http://svo2.cab.inta-csic.es/svo/theory/fps3 (JWST/NIRCam)
     -
   * - PanSTARRS1
     - PanSTARRS1
     - gp, rp, ip, zp, yp
     - Tonry et al. 2012, ApJ, 750, 99
     - :raw-html:`&check;`
   * - Pristine
     - Pristine
     - CaHK
     - Starkenburg E., Martin N., et al. 2017, MNRAS, 471, 2587
     -
   * - SDSS
     - SDSS
     - u, g, r, i, z
     - Doi et al. 2010, AJ, 141, 47
     - :raw-html:`&check;`
   * - Sky_Mapper
     - SkyMapper
     - u, u2, v, g, r, i, z
     - Bessel et al., 2011PASP..123..789B (u2 filter as in https://skymapper.anu.edu.au/data-release/#Filters)
     -
   * - Stromgren
     - Stromgren
     - u, v, b, y
     - http://svo2.cab.inta-csic.es/svo/theory/fps3/ (INT/WFC)
     - :raw-html:`&check;` :raw-html:`&ast;`
   * - WFIRST
     - WFIRST
     - R062, Z087
     - http://svo2.cab.inta-csic.es/svo/theory/fps3 (WFIRST)
     -

The complete list of the systems included in the package can also be obtained as follows:

.. code-block:: python

    from gaiaxpy import PhotometricSystem

    PhotometricSystem.get_available_systems()

Users can request the addition of other photometric systems by raising an issue via GitHub.
The main conditions for adding a new system are the following:

* Requests need to be properly justified. An example: it would be pointless to include a specific set of passbands that is used at a given telescope to approximate the JKC or SDSS systems. Synthetic magnitudes/fluxes (standardised or non-standardised) in these systems can be already obtained with GaiaXPy. On the other hand, it would be useful to include a set of passbands adopted by an existing or forthcoming survey that intends to provide magnitudes in its own “natural” photometric system, or a set aimed at tracing a specific feature/characteristic of the available XP spectra, not covered by already included passbands.
* The newly added systems will be publicly available to all GaiaXPy users
* The new system to be added is specified as follows:

  * one csv file per passband, containing the following columns: wavelength in nm or Angstrom, total response in arbitrary units
  * it must be clearly specified if the transmission curves are photonic curves or energy curves (see, e.g., Bessell & Murphy 2012)
  * it must be clearly specified if the desired magnitudes are VEGAMAG or AB mag
  * a reference for the source of all the above info (especially the transmission curves) must be provided.

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

All the available options are described in :ref:`plot_spectra <plotter>`.
