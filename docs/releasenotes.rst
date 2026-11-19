Release notes
=============

.. _releasenotes:

Version 2.2.0
-------------

Released on 2026/11/19.

**Breaking changes**

* Built-in photometric-system identifiers now include the Gaia data release.
  For example, ``PhotometricSystem.JKC`` has been renamed to
  ``PhotometricSystem.DR3_JKC``, and ``PhotometricSystem.SDSS`` to
  ``PhotometricSystem.DR3_SDSS``. Update scripts that refer to these
  identifiers. Use ``PhotometricSystem.get_available_systems()`` to inspect
  the identifiers available in the installed version. Gaia DR3 is the only
  supported data release in 2.2.0; the new naming convention prepares for
  future multi-release support.
* User-defined photometric systems have release- and version-specific
  identifiers, such as ``PhotometricSystem.USER_DR3_Example_v1``. Scripts
  referring to previously loaded additional systems may need to update
  their names. Check any code that relies on generated photometry column
  names when migrating to versioned additional systems.

**New functionality**

* Added processing provenance metadata, including the GaiaXPy version,
  processing operation and relevant configurations. Metadata are retained
  in supported output formats. Added metadata support for synthetic
  photometry, including relevant standardisation and error-correction configurations.
* Added support for gzip-compressed CSV, ECSV, FITS and XML/VOTable inputs,
  and ZIP files as downloaded from the Gaia Archive.
* Added ``get_required_columns()`` to describe the publicly supported
  input columns for GaiaXPy operations.
* Added versioned user-defined photometric systems and improved their
  discovery, loading and management.

**Bug fixes**

* Fixed the computation of correlation matrices returned by ``calibrate()`` when ``with_correlation=True``, ensuring consistency with the propagated covariance matrix.
* Fixed plotting issues when the input DataFrame has a non-consecutive or otherwise modified index.
* Improved handling of missing BP or RP spectra when plotting, ensuring consistent source colours across panels.

**Improvements**

* Improved input handling for DataFrames, individual spectra, ZIP archives,
  queries and source-ID selections.
* Improved file output and overwrite controls.
* Improved Archive authentication options, including credentials files and
  interactive password entry.

Version 2.1.5
-------------

Released on 2026/10/15.

* Added a fix for GACS 3.15: `PR #152 <https://github.com/gaia-dpci/GaiaXPy/pull/152>`_
* Removed support for Python 3.10 and added support for Python 3.15.

Version 2.1.4
-------------

Released on 2025/12/15.

* Exposed the truncation parameter in the generator: `PR #145 <https://github.com/gaia-dpci/GaiaXPy/pull/145>`_
* Documented additional known issues: `PR #148 <https://github.com/gaia-dpci/GaiaXPy/pull/148>`_

Version 2.1.3
-------------

Released on 2025/12/10.

* Added basis truncation to the synthetic photometry generator: `PR #110 <https://github.com/gaia-dpci/GaiaXPy/pull/110>`_
* Improved package installation and raised the minimum Python version to 3.10: `PR #130 <https://github.com/gaia-dpci/GaiaXPy/pull/130>`_
* Fixed slow import when Archive is unavailable: `PR #140 <https://github.com/gaia-dpci/GaiaXPy/pull/140>`_
* Added LaTeX labels to plots: `issue #80 <https://github.com/gaia-dpci/GaiaXPy/issues/80>`_

Version 2.1.2
-------------

Released on 2024/06/12.

* Fixed issue with loading a nested directory with additional systems: `issue #100 <https://github.com/gaia-dpci/GaiaXPy/issues/100>`_
* Fixed issue with substrings in additional system names: `issue #102 <https://github.com/gaia-dpci/GaiaXPy/issues/102>`_
* Removed unnecessary restriction in error correction: `issue #103 <https://github.com/gaia-dpci/GaiaXPy/issues/103>`_
* Added internal query marker: `issue #106 <https://github.com/gaia-dpci/GaiaXPy/issues/106>`_

Version 2.1.1
-------------
Released on 2024/05/03.

* Fixed incompatibility with Archive output affecting ADQL queries: `issue #91 <https://github.com/gaia-dpci/GaiaXPy/issues/91>`_
* Removed Python 3.7 support, added Python 3.12 support: `issue #81 <https://github.com/gaia-dpci/GaiaXPy/issues/81>`_
* Modified converter output for sources with a missing band: `issue #78 <https://github.com/gaia-dpci/GaiaXPy/issues/78>`_
* Modified generator output for sources with a missing band: `issue #79 <https://github.com/gaia-dpci/GaiaXPy/issues/79>`_
* Fixed bug specific to additional systems and GaiaDR3Vega: `issue #83 <https://github.com/gaia-dpci/GaiaXPy/issues/83>`_
* Removed some conditions on additional filters file names: `issue #72 <https://github.com/gaia-dpci/GaiaXPy/issues/72>`_

Version 2.1.0
-------------
Released on 2023/08/11.

* Removed support for Python 3.6.
* Updated output files to comply with the standards described in issues `#51 <https://github.com/gaia-dpci/GaiaXPy/issues/51>`_ and `#52 <https://github.com/gaia-dpci/GaiaXPy/issues/52>`_.
* Improved the performance of the main tools by up to 9 times. The table below summarises the results.

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

* Made Cosmos credentials optional for source ID lists and queries.

Version 1.1.1
-------------
Released on 2022/06/13.

* Switched queries to the official Gaia Archive.
* Updated Hipparcos-Tycho bases.
* Added fix for single band source with lists and queries.
* Added error correction tables for ``Gaia_DR3_Vega``, ``Els_Custom_W09_S2``, ``Pristine`` and ``Sky_Mapper``.
* Fixed an error-correction bug when a regular system and its standardised version were requested for the same DataFrame.

Version 1.1.0
-------------
Released 2022/06/08.

* Fixed error correction bug in system ``HST_ACSWFC``.
* Fixed error when passing a single PhotometricSystem to error correction.
* Added SkyMapper filter.
* Fixed Windows compatibility.
* Removed the u band from the standardised Stromgren system. (See Gaia Collaboration, Montegriffo et al. 2022 for more details.)

Version 1.0.2
-------------
Released on 2022/05/22.

* Fixed error in ECSV output by adding the missing headers file.

Version 1.0.1
-------------
Released on 2022/05/22.

* Released in error and marked to be ignored by the installer.

Version 1.0.0
-------------
Released on 2022/05/19.

* Initial release.
