# GaiaXPy

GaiaXPy is a Python library to facilitate handling Gaia BP/RP spectra as distributed from the [Gaia archive](https://gea.esac.esa.int/archive/).

BP/RP (often shortened as XP) spectra will become available for the first time in Gaia Data Release 3 (DR3).
In their first release, only source **mean spectra** will be available: these are spectra that have been generated
from a number of single observations of the same object. **Epoch spectra**, i.e. spectra consisting of one single
observation, will become available in future releases.

Two reference systems are defined by the data processing:
* the **internal system** describes the response of the average instrument and covers homogeneously all different
observing conditions (time, field of view, location on the focal plane, instrument configuration); **internally
calibrated spectra** have units of electrons per second per pixel sample.
* the **external or absolute system** is the commonly used reference system where the spectrum is defined in units
of W nm<sup>-1</sup>m<sup>-2</sup> on a scale of absolute wavelengths.

### Mean spectra

The mean spectra available from the archive are continuously defined as an array of coefficients to be applied to
a set of basis functions.
Depending on the set of bases in use, it is possible to represent both internally and externally calibrated
spectra using the same array of coefficients (and correlation matrix).

For many practical use cases, it is convenient to sample the continuously defined spectra on a grid of positions.
These will be pseudo-wavelengths in the case of internally calibrated spectra, and absolute wavelength in the case
of externally calibrated spectra.

### What can GaiaXPy do for you?

The GaiaXPy library will grow in time. For Gaia DR3 the following functionalities are covered:
* **Calibration** of internally-calibrated continuously-represented mean spectra to the absolute system. An absolute spectrum sampled on a user-defined or default wavelength grid is created for each set of BP and RP input spectra, that will be combined into one single absolute spectrum covering the entire wavelength range covered by BP and RP. If either band is missing, the output spectrum will only cover the range covered by the available data.
* **Conversion** of mean spectra from a continuous representation to a sampled spectrum, optionally on a user-defined grid of positions. The output spectrum will be in the internal system (if an absolute spectrum is required, please use the Calibration functionality). 
* **Generation** of synthetic photometry in bands that are covered by the BP/RP wavelength range. Several sets of filters are included in the package.
* **Simulation** of Gaia BP/RP internally calibrated spectra starting from an input Spectral Energy Distribution (SED) given the Gaia DR3 instrument model.

## Installation

GaiaXPy is not available through a package manager yet, and therefore needs to be manually installed.

To install GaiaXPy, Python3 is required, and creating a virtual environment is recommended:

```sh
# Move to the package directory
cd GaiaXPy
# Create a virtual environment
python3 -m venv .env
# Activate the environment
source .env/bin/activate
# Install package requirements
pip install -r requirements.txt
# Install the GaiaXPy package in interactive mode
pip install -e .
```

If the previous steps succeed, then GaiaXPy is correctly installed.

## Usage

The package currently includes five different functionalities: a **calibrator**, a **converter**, a **simulator**, a **synthetic photometry generator** and a **plotter**.

### Calibrator

```python
from gaiaxpy import calibrate
mean_spectrum_file = 'path/to/mean_spectrum_with_correlation.csv'
calibrated_data = calibrate(mean_spectrum_file, save_file=False)
```
The method `calibrate` returns a list with the calibrated spectra, and creates
a file with the data unless `save_file` is `False`. The output file, by default, has the same extension as the input file but it is possible to choose a different output format which can be either `'.avro'`, `'.csv'`, `'.fits'`, or `'.xml'`. The output file name is `'output_spectra'` by default, but the user can choose a different one.

```python
calibrated_data = calibrate(mean_spectrum_file, output_file='my_output_name',
output_format='.fits')
```

**If an output file with the same name as an existing one is created, the data of the previous file is automatically overwritten.**

### Converter

```python
from gaiaxpy import convert

mean_spectrum_file = 'path/to/mean_spectrum_with_correlation.csv'
converted_data = convert(mean_spectrum_file, save_file=False)
```
The method convert returns a list, where each element corresponds to a converted
spectrum, and creates a file with this data, unless `save_file` is set to `False`. The output file has the same extension as the input one (in the example above, `'.csv'`) and the default output file name is `'output_spectra'`. There is also a default sampling which is `numpy.linspace(0, 60, 600)`.

It is possible to choose the output format (`'.avro'`, `'.csv'`, `'.fits'`, `'.xml'`), the name of the output file and a custom sampling.
```python
converted_data = convert(mean_spectrum_file, sampling=numpy.linspace(0, 100, 1000),
 output_file='my_output_name', output_format='.xml')
```
**If an output file with the same name as an existing one is created, the data of the previous file is automatically overwritten.**

### Simulator

The simulator functionality allows the user to simulate sampled or continuous internally calibrated spectra from an input Spectral Energy Distribution (SED).

The input SED must be a CSV file with one line per `source ID` and the following format:

```python
source_id,wl,flux,flux_error
12345,"(300.000,300.100,1199.80)","(6.410e-15,6.406e-15,6.398e-15)","(0.00000,0.00000,0.00000)"
98765,"(300.000,300.200,1200.00)","(6.430e-15,6.646e-15,6.864e-15)","(0.00000,0.00000,0.00000)"
```

To simulate sampled spectra:

```python
import numpy as np
from gaiaxpy import simulate_sampled

sed_file = 'path/to/sed.csv'
sampled_data = simulate_sampled(sed_file, sampling=np.linspace(0, 60, 600), save_file=False)
```

The function `simulate_sampled` requires a sampling which is `numpy.linspace(0, 60, 600)` by default.

To simulate continuous spectra:

```python
from gaiaxpy import simulate_continuous

sed_file = 'path/to/sed.csv'
continuous_data = simulate_continuous(sed_file, save_file=False)
```

**If an output file with the same name as an existing one is created, the data of the previous file is automatically overwritten.**

### Synthetic photometry generator

```python
from gaiaxpy import generate, PhotometricSystem
mean_spectrum_file = 'path/to/mean_spectrum_with_correlation.csv'
phot_system = PhotometricSystem.JOHNSON
generated_data = generate(mean_spectrum_file, phot_system, save_file=False)
```
The synthetic photometry utility uses the method `generate` to return a list with the generated synthetic photometry results. The synthetic fluxes are given in units
of W nm<sup>-1</sup>m<sup>-2</sup>. A file containing the ouput data is created, unless `save_file` is set to False. By default, the file has the same extension as the input file but the output format can be either `'.avro'`, `'.csv'`, `'.fits'`, or `'.xml'`. The output file name is `'output_synthetic_photometry'` by default, but the user can choose a different one.
```python
generated_data = generate(mean_spectrum_file, phot_system,
  output_file='my_output_name', output_format='.xml')
```
**Currently, the systems available are Gaia DR3 (Vega and AB), Johnson-Cousins, SDSS and [SDSS Doi](https://ui.adsabs.harvard.edu/abs/2010AJ....139.1628D/abstract).

**If an output file with the same name as an existing one is created, the data of the previous file is automatically overwritten.**

### Plotter
```python
from gaiaxpy import plot_spectra
plot_spectra(output, multi=False, show_plot=True, output_path='/path')
```

This functionality allows to plot the output of the `calibrator`, `converter` and `synthetic photometry generator`. The parameter `multi` set as `True` plots all the results in one image, whereas `False` generates one image per spectrum in `output`. The parameter `show_plot` shows the images if it is set as `True`. If a `output_path` is provided, the plots are saved.

## License
[GNU](https://gitlab.com/pyxp-developers/gaiaxpy-pkg/-/blob/master/LICENSE)
