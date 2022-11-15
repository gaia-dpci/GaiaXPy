About the package
=================

General description
-------------------

GaiaXPy is a Python library to facilitate handling Gaia BP/RP spectra as distributed from the `Gaia archive <https://gea.esac.esa.int/archive/>`_.

BP/RP (often shortened as XP) spectra became available for the first time in Gaia Data Release 3 (DR3).
In their first release, only source **mean spectra** are available: these are spectra that have been generated from a number of single observations of the same object. **Epoch spectra**, i.e. spectra consisting of one single observation, will become available in future releases.

Two reference systems are defined by the data processing:

- The **internal system** describes the response of the average instrument and covers homogeneously all different observing conditions (time, field of view, location on the focal plane, instrument configuration); **internally calibrated spectra** have units of electrons per second per pixel sample.
- The **external or absolute system** is the commonly used reference system where the spectrum is defined in units of W nm :superscript:`-1` m :superscript:`-2` on a scale of absolute wavelengths.

Mean spectra
------------

The mean spectra available from the archive are continuously defined as an array of coefficients to be applied to a set of basis functions.
Depending on the set of bases in use, it is possible to represent both internally and externally calibrated spectra using the same array of coefficients (and correlation matrix).

For most practical use cases, it is convenient to sample the continuously defined spectra on a grid of positions.
These will be pseudo-wavelengths in the case of internally calibrated spectra, and absolute wavelength in the case of externally calibrated spectra.

What can GaiaXPy do for you?
----------------------------

The GaiaXPy library will grow in time. For Gaia DR3 the following functionalities are covered:

- **Calibration** of internally-calibrated continuously-represented mean spectra to the absolute system. An absolute spectrum sampled on a user-defined or default wavelength grid is created for each set of BP and RP input spectra, that will be combined into one single absolute spectrum covering the entire wavelength range covered by BP and RP. If either band is missing, the output spectrum will only cover the range covered by the available data.
- **Conversion** of mean spectra from a continuous representation to a sampled spectrum, optionally on a user-defined grid of positions. The output spectrum will be in the internal system (if an absolute spectrum is required, please use the Calibration functionality).
- **Generation** of synthetic photometry in bands that are covered by the BP/RP wavelength range. Several sets of filters are included in the package.

A further functionality is being developed and will be released soon:

- **Simulation** of Gaia BP/RP internally calibrated spectra starting from an input Spectral Energy Distribution (SED) given the Gaia DR3 instrument model.
