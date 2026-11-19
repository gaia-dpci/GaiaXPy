# GaiaXPy

GaiaXPy is a Python package for working with Gaia Data Release 3 (DR3) XP (BP/RP) spectra. After 2nd December 2026,
newer versions will also support Gaia DR4 XP spectra.

| Task | GaiaXPy tool |
| --- | --- |
| Sample continuous XP coefficients in pseudo-wavelength | `convert` |
| Reconstruct a flux spectrum on a wavelength grid in nm | `calibrate` |
| Compute synthetic photometry, including magnitudes, fluxes and flux errors | `generate` |
| Correct synthetic photometry flux errors where correction tables are available | `generate` with `error_correction=True`, or `apply_error_correction` |
| Plot sampled spectra | `plot_spectra` |

Input supports CSV, ECSV, FITS and XML/VOTable, including GZIP and ZIP files, as well as Gaia Archive source-ID lists
and tuples, ADQL queries and pandas DataFrames.

## Installation

To install the public release from PyPI:

```sh
pip install GaiaXPy
```

For a development or pre-release version, see the [installation guide](https://gaiaxpy.readthedocs.io/en/latest/installation.html).

## Documentation and tutorials

- [GaiaXPy homepage and tutorials](https://gaia-dpci.github.io/GaiaXPy-website/)
- [GaiaXPy documentation](https://gaiaxpy.readthedocs.io/en/latest/)
- [Gaia Archive](https://archives.esac.esa.int/gaia/)

## Questions and feedback

For questions, bug reports or feature requests, use the [GitHub issue tracker](https://github.com/gaia-dpci/GaiaXPy/issues).
Bug reports should include the GaiaXPy and Python versions, the function call,
the complete error message and a small example that reproduces the issue.

## Citation

Cite the DOI corresponding to the GaiaXPy version used in your analysis.
See the [citation guide](https://gaiaxpy.readthedocs.io/en/latest/cite.html) for version-specific DOIs and references.

From version 2.2.0 onwards, GaiaXPy also includes metadata in its outputs to support reproducibility and traceability,
recording information about the processing run, and relevant configuration details. Find the relevant tutorial
in the [GaiaXPy website](https://gaia-dpci.github.io/GaiaXPy-website/tutorials.html).

## Licence

[BSD 3-Clause](LICENCE).
