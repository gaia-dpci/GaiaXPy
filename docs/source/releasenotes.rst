Release notes
=============

.. _releasenotes:

Version 2.1.0
-------------
Released on 2023/08/10.

* Output files modified to comply with standards, according to issues `#51 <https://github.com/gaia-dpci/GaiaXPy/issues/51>`_ and `#52 <https://github.com/gaia-dpci/GaiaXPy/issues/52>`_.
* Speed improvements on the main tools of up to 9x. The main results are summarised in the table below.

The table shows the processing time speed up factors (i.e. excluding input reading and output storing) according to input format and tool or function.

The speed up factors were computed as ``old_time / new_time``. So, for example, a factor of ``2.00``, means that the code in
the new version of the packages runs twice as fast as in the old version.

.. table:: Speed up factor by format and function
   :widths: 20 20 20 20 20

   +-----------------+-----------+---------+---------------------------+--------------------------+
   | Format/Function | Calibrate | Convert | Generate (w/o error_corr) | Generate (w/ error_corr) |
   +=================+===========+=========+===========================+==========================+
   | CSV             |      8.94 |    8.97 |                      2.28 |                     2.80 |
   +-----------------+-----------+---------+---------------------------+--------------------------+
   | ECSV            |      8.98 |    8.93 |                      2.39 |                     2.73 |
   +-----------------+-----------+---------+---------------------------+--------------------------+
   | FITS            |      8.74 |    9.08 |                      2.35 |                     2.73 |
   +-----------------+-----------+---------+---------------------------+--------------------------+
   | XML binary      |      9.41 |    9.13 |                      3.40 |                     2.88 |
   +-----------------+-----------+---------+---------------------------+--------------------------+
   | XML plain       |      9.23 |    8.99 |                      2.34 |                     2.82 |
   +-----------------+-----------+---------+---------------------------+--------------------------+

* More detailed speed improvements results can be found :ref:`here <improvements>`.

Version 2.0.1
-------------
Released on 2023/01/24.

* Fixed issue in function for computing the inverse of the covariance matrix (``get_inverse_covariance_matrix``).
* Fixed issue in function to get chi-squared from an input inverse square root of covariance matrix (``get_chi2``).
* Added function to compute the inverse square root of the covariance matrix (``get_inverse_square_root_covariance_matrix``).

Version 2.0.0
-------------
Released on 2023/01/11.

* Added functionality to load external files that contain photometric systems.

Version 1.2.4
-------------
Released on 2023/01/09.

* Fixed problem in the application of the flux offset for the standardised system PanSTARRS1 (``PhotometricSystem.PanSTARRS1_Std``). The flux offset is part of the standardisation process described in Section 2.2.1 and equation 13 in `Gaia Collaboration, Montegriffo, et al., 2022 <https://ui.adsabs.harvard.edu/abs/2022arXiv220606215G/abstract>`_. In previous versions no flux offset was applied to the flux. Flux error and magnitude were derived consistently.
* Replaced SDSS filters (available as ``PhotometricSystem.SDSS``) with those defined in `Doi et al. 2010, AJ, 141, 47 <https://ui.adsabs.harvard.edu/abs/2010AJ....139.1628D/abstract>`_. Note that the standardised version (``PhotometricSystem.SDSS_Std``) was already based on Doi et al. 2010, AJ, 141, 47 and is therefore unchanged with respect to previous versions of GaiaXPy.

Version 1.2.3
-------------
Released on 2022/11/28.

* Removed matplotlib version constraint.

Version 1.2.2
-------------
Released on 2022/11/22.

* Removed fastavro version constraint.
* Fixed bug in calibrator with truncation (only RP value was being used).

Version 1.2.1
-------------
Released on 2022/11/28.

* Added LSST filter.

Version 1.2.0
-------------
Released on 2022/08/22.

* Added Cholesky functionality: inverse covariance matrix, chi-squared.
* Improved testing.
* Replaced custom progress tracker by tqdm.
* Improved performance of calibrator, converter, and generator.

Version 1.1.4
-------------
Released on 2022/06/21.

* Added DECam system files.
* Removed RVS band from Gaia DR3 system.
* Added table of available systems in documentation.
* Added info for requesting new systems and updated citations.

Version 1.1.3
-------------
Released on 2022/06/16.

* Fixed legend bug in plotter.
* Restricted pandas version, >= 1.0.0.

Version 1.1.2
-------------
Released on 2022/06/14.

* Cosmos credentials are optional when using lists and queries.

Version 1.1.1
-------------
Released on 2022/06/13.

* Query official Gaia Archive.
* Updated Hipparcos-Tycho bases.
* Added fix for single band source with lists and queries.
* Added error correction tables for ``Gaia_DR3_Vega``, ``Els_Custom_W09_S2``, ``Pristine`` and ``Sky_Mapper``.
* Fixed but in error correction caused when a regular system and its standardised version where requested on the same data frame.

Version 1.1.0
-------------
Released 2022/06/08.

* Fixed error correction bug in system ``HST_ACSWFC``.
* Fixed error when passing a single PhotometricSystem to error correction.
* Added SkyMapper filter.
* Fixed Windows compatibility.
* The u band has been removed from the standardised Stromgren system. (See Gaia Collaboration, Montegriffo et al. 2022 for more details.)

Version 1.0.2
-------------
Released on 2022/05/22.

* Fixed error in ECSV output by adding the missing headers file.

Version 1.0.1
-------------
Released on 2022/05/22.

* Erroneous release, will be ignored by the installer.

Version 1.0.0
-------------
Released on 2022/05/19.

* Initial release.
