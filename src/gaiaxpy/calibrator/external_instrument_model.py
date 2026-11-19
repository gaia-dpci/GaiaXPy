"""Store dispersion, response and inverse bases for external calibration.

The model provides tabulated wavelength-to-pseudo-wavelength coordinates and
instrument response, together with coefficients used to reconstruct calibrated
spectra. The calibration pipeline uses these components for custom sampling.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import interpolate


class ExternalInstrumentModel:
    """Hold the external calibration components for one photometer.

    The model stores the supplied tables and inverse-basis parameters. Its response
    and coordinate methods interpolate the tables at requested wavelengths.
    """

    def __init__(self, dispersion: dict, response: dict, bases: "pd.DataFrame"):
        """Store the dispersion, response and inverse-basis configuration.

        Args:
            dispersion (dict): One-dimensional arrays under wavelength (nm) and
                pseudo-wavelength, defining the dispersion relation.
            response (dict): One-dimensional wavelength (nm) and response arrays.
            bases (pandas.Series): Inverse-basis counts, normalisation parameters
                and coefficient arrays, as loaded by from_config_npz.
        """
        self.dispersion = dispersion
        self.response = response
        self.bases = bases

    @classmethod
    def from_config_npz(cls, dispersion_path: Path, response_path: Path, bases_path: Path):
        """Load the three NPZ components of one photometer's calibration model.

        Args:
            dispersion_path (str or pathlib.Path): NPZ file whose data array contains
                wavelength in row zero and pseudo-wavelength in row one.
            response_path (str or pathlib.Path): NPZ file whose data array contains
                wavelength in row zero and instrument response in row one.
            bases_path (str or pathlib.Path): NPZ file containing inverse-basis
                parameters and flattened coefficient arrays.

        Returns:
            ExternalInstrumentModel: Loaded tables and a pandas.Series of basis
            parameters. inverseBasesCoefficients has shape
            (nBases, nInverseBasesCoefficients), and transformationMatrix has shape
            (nBases, nTransformedBases).

        Raises:
            OSError: A configuration file cannot be opened or read.
            KeyError: An expected NPZ field is missing.
            ValueError: Array sizes do not match the declared basis dimensions,
                or an archive cannot be loaded.

        Notes:
            Scalar basis fields are converted to scalar values and array fields are
            copied into memory before the archives are closed. The embedded
            __gaiaxpy_metadata__ field is excluded from the numeric basis parameters;
            the calling calibration pipeline records configuration metadata separately.
        """
        with np.load(dispersion_path, allow_pickle=False) as archive:
            values = archive['data']
            dispersion = {
                'wavelength': values[0],
                'pseudo-wavelength': values[1],
            }

        with np.load(response_path, allow_pickle=False) as archive:
            values = archive['data']
            response = {
                'wavelength': values[0],
                'response': values[1],
            }

        with np.load(bases_path, allow_pickle=False) as archive:
            bases = pd.Series({
                key: archive[key].item() if archive[key].ndim == 0 else archive[key].copy()
                for key in archive.files if key != '__gaiaxpy_metadata__'
            })

        bases['inverseBasesCoefficients'] = bases['inverseBasesCoefficients'].reshape(
            int(bases['nBases']), int(bases['nInverseBasesCoefficients']))
        bases['transformationMatrix'] = bases['transformationMatrix'].reshape(
            int(bases['nBases']), int(bases['nTransformedBases']))

        return cls(dispersion, response, bases)

    def get_response(self, wavelength: float) -> "np.ndarray":
        """Interpolate the tabulated instrument response at wavelengths in nm.

        Args:
            wavelength (float or array-like): Wavelength or wavelengths in nm.

        Returns:
            numpy.ndarray: Interpolated response. A scalar wavelength gives a
            zero-dimensional array; array input retains its corresponding shape.

        Notes:
            Each call constructs an interpolating cubic spline with s=0 from the
            stored response table. Values outside the tabulated wavelength range
            are extrapolated. Invalid table data raise errors from the spline fitter.
        """
        tck = interpolate.splrep(self.response.get('wavelength'), self.response.get('response'), s=0)
        return interpolate.splev(wavelength, tck, der=0)

    def wl_to_pwl(self, wavelength: float) -> "np.ndarray":
        """Convert wavelengths in nm to pseudo-wavelength coordinates using the model.

        Args:
            wavelength (float or array-like): Wavelength or wavelengths in nm.

        Returns:
            numpy.ndarray: Pseudo-wavelength coordinates. A scalar wavelength gives
            a zero-dimensional array; array input retains its corresponding shape.

        Notes:
            Each call constructs an interpolating cubic spline with s=0 from the
            stored dispersion table. Values outside its wavelength range are
            extrapolated. Invalid table data raise errors from the spline fitter.
        """
        tck = interpolate.splrep(self.dispersion.get('wavelength'), self.dispersion.get('pseudo-wavelength'), s=0)
        return interpolate.splev(wavelength, tck, der=0)
