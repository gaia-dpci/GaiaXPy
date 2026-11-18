"""Produce calibrated flux and flux-error samples from continuous BP/RP spectra.

Default sampling uses the stored grid, design matrices and merge weights for
the resolved Gaia release. Custom sampling evaluates the configured instrument
models and calculates BP/RP merge weights at the supplied wavelengths. Results
contain one spectrum per input source, with optional correlations between samples.
"""
from pathlib import Path
from sys import stdout
from typing import Union, Tuple

import numpy as np
from tqdm import tqdm

from gaiaxpy.core.config import load_xpmerge_from_file, load_xpsampling_from_file
from gaiaxpy.core.generic_functions import (cast_output, validate_wl_sampling, parse_band,
                                            format_sampled_output)
from gaiaxpy.core.generic_variables import pbar_colour, pbar_units, pbar_message, INV_BASIS_TYPES
from gaiaxpy.core.output_metadata import OUTPUT_METADATA_KEY, collect_output_metadata
from gaiaxpy.core.release_resolution import parse_release
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.output.sampled_spectra_data import SampledSpectraData
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.utils import get_covariance_matrix
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum
from .external_instrument_model import ExternalInstrumentModel
from ..core.config_dispatcher import CalibratorDispatcher
from ..core.dispersion_function import wl_range
from ..core.input_validator import validate_save_arguments, validate_overwrite
from ..spectrum.calibration_absolute_sampled_spectrum import CalibrationAbsoluteSampledSpectrum

__FUNCTION_KEY = 'calibrator'


def calibrate(input_object: Union[list, tuple, Path, "pd.DataFrame", "pd.Series", str], sampling: "np.ndarray" = None,
              truncation: bool = False, output_path: Union[Path, str] = '.', output_file: str = 'output_spectra',
              output_format: str = None, save_file: bool = True,
              with_correlation: bool = False, username: str = None, password: str = None,
              credentials_file: str | Path = None, release: str | None = None, *,
              disable_info: bool = False, basis_type: str = INV_BASIS_TYPES.basic, overwrite="yes") -> ("pd.DataFrame",
                                                                                                        "np.ndarray"):
    """Calibrate continuous BP/RP mean spectra onto a common wavelength grid.

    Args:
        input_object (str, pathlib.Path, pandas.DataFrame, pandas.Series, list or tuple): Input
            continuous spectra. Supply a local file, a DataFrame,
            a single spectrum row as a Series, a list or tuple
            of source IDs supplied as integers or integer strings, or an ADQL query.
            Supported file formats are
            CSV, ECSV, FITS, and XML/VOTable, including supported gzip
            inputs and Archive ZIP files. Source ID selections and queries
            retrieve spectra from the Archive.
        sampling (numpy.ndarray or None): One-dimensional, increasing wavelength
            grid in nm, with at least two positions in the range [330, 1050].
            Supplying a grid evaluates the instrument model at those wavelengths.
            None uses the grid stored in the calibration configuration for the
            resolved release: 336–1020 nm in steps of 2 nm (343 samples). Both endpoints are included.
        basis_type (str): Inverse basis set to use. The only supported type is 'basic' for DR3.
        truncation (bool): Use the recommended number of basis functions for
            each source and photometer. When True, retain bp_n_relevant_bases
            functions for BP and rp_n_relevant_bases for RP, using the counts
            in that source's input row. When False, use all available basis
            functions. Non-positive counts leave that photometer untruncated.
        output_path (str or pathlib.Path): Destination directory when saving.
            Missing directories are created by the selected writer.
        output_file (str): Output filename stem without an extension. The default
            is 'output_spectra'.
        output_format (str or None): 'csv', 'ecsv', 'fits' or 'xml'
            (VOTable), ignoring case and an initial dot. If omitted, use the
            underlying input format; for example, .csv.gz input selects CSV output.
            DataFrame and Archive inputs default to CSV.
        overwrite (str): 'yes' or 'y' replaces existing files (default: 'yes').
            'no' or 'n' raises FileExistsError if any output exists. 'ask' prompts
            once before replacing existing files. Values are case-insensitive.
            Declining skips saving. With save_file=False, 'ask' emits a warning unless disable_info=True.
        save_file (bool): Write the results and wavelength sampling to disk.
            False returns them without writing; supplying output_file or
            output_format in that case may produce a warning.
        with_correlation (bool): Add correlations between the output flux samples.
        username (str or None): Cosmos username for Archive access.
        password (str or None): Cosmos password, supplied with username when
            authenticating through these arguments.
        credentials_file (str or pathlib.Path or None): UTF-8 file with username
            and password on separate lines. Cannot be combined with username
            or password. Without supplied credentials, the Archive reader may
            request an interactive login when authentication is needed.
        release (str or None): Gaia release. Defaults to 'dr3' when not specified.
            When identifiable, the input release must match the selected release.
        disable_info (bool): Suppress routine reading, progress and saving
            messages, including Archive information. Warnings, errors and
            required login prompts remain visible.

    Returns:
        tuple[pandas.DataFrame, numpy.ndarray]: Calibrated spectra and the common
        wavelength grid in nm. The table contains source_id, flux and flux_error,
        with one array per source for each sampled field. Flux and flux error
        use W nm^-1 m^-2. With with_correlation=True, correlation contains the
        packed lower triangle of the sample correlation matrix, excluding its
        diagonal. The data_type attr identifies the spectrum representation.
        The gaiaxpy_metadata attr records the release, configuration files,
        package version, basis type and input correction status.

    Raises:
        ValueError: The sampling endpoints are not increasing or lie outside
            [330, 1050]; the input and requested releases disagree; or
            coefficient and basis dimensions differ.
        InvalidReleaseError: A supplied release label is not recognised.
        NoBandsAvailableError: A source has neither BP nor RP data available
            for calibration.
        FileNotFoundError: An input or required configuration file does not exist.

    Notes:
        When both photometers are available, their contributions are combined
        using the BP/RP merge weights. For BP-only input, values at or above
        the configured upper BP wavelength limit are NaN. For RP-only input,
        values at or below the lower RP limit are NaN. Corresponding flux errors
        and correlation entries are also missing; the wavelength grid is retained.

        When save_file=False, return the spectra and wavelength grid without
        writing files. Processing metadata remains attached to the returned DataFrame.
        CSV saving writes <output_file>.csv, <output_file>_sampling.csv and
        <output_file>_metadata.csv. ECSV, FITS and XML/VOTable embed the
        sampling and metadata in the main output. Existing output files are
        overwritten by default. Avro input and output are also available for internal use.
        The Gaia Archive does not distribute Avro files.
    """
    overwrite = validate_overwrite(overwrite)
    return _calibrate(input_object, sampling, truncation=truncation,
                      output_path=output_path, output_file=output_file, output_format=output_format,
                      save_file=save_file, with_correlation=with_correlation, username=username, password=password,
                      credentials_file=credentials_file, release=release, disable_info=disable_info,
                      basis_type=basis_type, overwrite=overwrite)


def _calibrate(input_object: Union[list, Path, str], sampling: "np.ndarray" = None, truncation: bool = False,
               output_path: Union[Path, str] = '.', output_file: str = 'output_spectra',
               output_format: str = None, save_file: bool = True, with_correlation: bool = False, username: str = None,
               password: str = None, credentials_file: str | Path = None,
               disable_info: bool = False, release: str = None, basis_type=INV_BASIS_TYPES.basic, *, overwrite="yes") \
        -> ("pd.DataFrame", "np.ndarray"):
    """Read, calibrate and optionally save continuous BP/RP mean spectra.

    Input, sampling, truncation, correction, correlation, Archive and output
    arguments have the same meanings as in the function 'calibrate'.

    Args:
        basis_type (str): Internal inverse-basis selection. DR3 supports only 'basic'.
        release (str or None): Gaia release, resolved through InputReader using
            the same rules as calibrate.
        disable_info (bool): Suppress routine reading, progress and saving messages.

    Returns:
        tuple[pandas.DataFrame, numpy.ndarray]: Calibrated samples with processing
        metadata attached, and their wavelength grid in nm.
    """
    overwrite = validate_overwrite(overwrite)
    release = parse_release(release)
    validate_wl_sampling(sampling)
    basis_type = CalibratorDispatcher.verify_basis(basis_type, sampling, release)
    validate_save_arguments(_calibrate.__defaults__[3], output_file, _calibrate.__defaults__[4], output_format,
                            save_file)
    reader = InputReader(input_object, _calibrate, truncation=truncation, disable_info=disable_info, user=username,
                         password=password, release=release, credentials_file=credentials_file)
    parsed_input_data, extension, release = reader.read()
    # Get configuration file(s)
    config_files = CalibratorDispatcher().build(parsed_input_data=parsed_input_data, sampling=sampling,
                                                release=release, basis_type=basis_type)

    xp_design_matrices, xp_merge, sampling = __generate_xp_matrices_and_merge(sampling, config_files, release=release)
    spectra_df = __create_spectra(parsed_input_data, truncation, xp_design_matrices, xp_merge,
                                  release=release, with_correlation=with_correlation,
                                  disable_info=disable_info)
    spectra_df = cast_output(spectra_df)
    spectra_df.attrs[OUTPUT_METADATA_KEY] = collect_output_metadata('calibrate', release, config_files,
                                                                    reader.applied_correction_files,
                                                                    basis_type=basis_type.lower())
    output_data = SampledSpectraData(spectra_df, sampling)
    output_data.save(save_file, output_path, output_file, output_format, extension, disable_info=disable_info,
                     overwrite=overwrite)
    return spectra_df, sampling


def _create_merge(xp: str, sampling: "np.ndarray", release) -> "np.ndarray":
    """Calculate one photometer's merge weights on a wavelength grid.

    Args:
        xp (str): BP or RP photometer, ignoring case.
        sampling (numpy.ndarray): One-dimensional wavelength positions in nm.
        release (str): 'dr3', selecting the configured BP/RP wavelength limits.

    Returns:
        numpy.ndarray: One weight per wavelength. Below the lower RP limit,
        BP has weight one and RP has weight zero. Above the upper BP limit,
        BP has weight zero and RP has weight one. Across that overlap, BP
        decreases linearly from one to zero and RP increases from zero to one.

    Raises:
        InvalidBandError: The photometer label is not recognised.
        InvalidReleaseError: The release label is not recognised.

    Notes:
        These weights are calculated for custom sampling. Default-grid
        calibration reads its stored weights from the configuration file.
    """
    xp = parse_band(xp)
    release = parse_release(release)
    bp_range = wl_range(BANDS.bp, release=release)
    rp_range = wl_range(BANDS.rp, release=release)

    wl_high = bp_range.high
    wl_low = rp_range.low

    def diff_element(wl):
        """Return the fractional position across the overlap for a wavelength in nm."""
        return (wl - wl_low) / (wl_high - wl_low)

    return np.array([1.0 if wl < wl_low else 0.0 if wl > wl_high else (1.0 - diff_element(wl)) for wl in sampling]) \
        if xp == BANDS.bp else np.array([0.0 if wl < wl_low else 1.0 if wl > wl_high else diff_element(wl) for wl in
                                         sampling])


def __generate_xp_matrices_and_merge(sampling: "np.ndarray", config_files: Union[dict, Path], release: str) -> \
        (dict, dict):
    """Load or evaluate the calibration bases, merge weights and wavelength grid.

    Args:
        sampling (numpy.ndarray or None): Custom wavelength grid in nm. None uses
            the stored grid and matrices: 336–1020 nm in steps of 2 nm (343 samples).
            Both endpoints are included.
        config_files (pathlib.Path, str or dict): For default sampling, the
            combined configuration file. For custom sampling, a dictionary
            keyed by 'bp' and 'rp', each containing dispersion, response and
            bases NPZ paths.
        release (str): Resolved Gaia release used for weights and basis evaluation.

    Returns:
        tuple[dict, dict, numpy.ndarray]: Per-band SampledBasisFunctions objects,
        per-band merge-weight arrays, and the common wavelength grid in nm.
        Each design matrix has one row per basis function and one column per
        wavelength sample.

    Raises:
        TypeError: Custom sampling is supplied but config_files is not a dictionary.
        KeyError: A required band or configuration entry is missing.

    Notes:
        Default sampling reads the stored XpSampling and XpMerge data. Custom
        sampling loads the two instrument models, calculates merge weights and
        evaluates the bases at the requested wavelengths. File-reading and
        model-configuration errors are reported to the caller.
    """

    def __get_xp_file_for_custom_sampling(xp: str, label: str) -> Path:
        """Find a configuration file for one photometer in the supplied dictionary.

        Args:
            xp (str): Lowercase 'bp' or 'rp'.
            label (str): 'dispersion', 'response' or 'bases'.

        Returns:
            pathlib.Path or str: Stored path for that band and component.

        Raises:
            KeyError: The photometer or component entry is missing.
        """
        return config_files[xp][label]

    if sampling is None:
        xp_sampling_grid, xp_merge = load_xpmerge_from_file(config_files)
        xp_design_matrices = load_xpsampling_from_file(config_files)
        xp_design_matrices = {xp: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_design_matrices[xp])
                              for xp in BANDS}
    else:
        if not isinstance(config_files, dict):
            raise TypeError('config_files must be a dictionary')

        xp_sampling_grid = sampling
        xp_merge = {xp: _create_merge(xp, sampling, release=release) for xp in BANDS}
        # Get CSV files
        ext_inst_model = {xp: ExternalInstrumentModel.from_config_npz(
            __get_xp_file_for_custom_sampling(xp, 'dispersion'),
            __get_xp_file_for_custom_sampling(xp, 'response'),
            __get_xp_file_for_custom_sampling(xp, 'bases')) for xp in BANDS}

        xml_bases_file = config_files.get('bases_file')

        xp_design_matrices = {xp: SampledBasisFunctions.from_external_instrument_model(
            xp_sampling_grid, xp_merge, ext_inst_model, xp, release=release,
            bases_file=xml_bases_file) for xp in BANDS}

    return xp_design_matrices, xp_merge, xp_sampling_grid


def __create_spectra(parsed_input_data: "pd.DataFrame", truncation: bool, design_matrices: dict,
                     merge: dict, release: str, with_correlation: bool = False, disable_info: bool = False) -> Tuple[
    "pd.DataFrame", "np.ndarray"]:
    """Calibrate and merge the available photometers for every parsed source.

    Args:
        parsed_input_data (pandas.DataFrame): Normalised continuous-spectrum
            data containing source_id, per-band coefficients, covariance
            information and standard_deviation.
        truncation (bool): Use the source's bp_n_relevant_bases count for BP and
            rp_n_relevant_bases count for RP. False uses all basis functions.
        design_matrices (dict[str, SampledBasisFunctions]): Per-band bases
            evaluated on the common wavelength grid.
        merge (dict[str, numpy.ndarray]): Per-band weights on that grid.
        release (str): Gaia release used for single-band wavelength limits.
        with_correlation (bool): Include packed correlations between output samples.
        disable_info (bool): Suppress the calibration progress bar.

    Returns:
        pandas.DataFrame: One row per input source in input order, with source_id,
        flux and flux_error, plus correlation when requested. The data_type attr
        identifies CalibrationAbsoluteSampledSpectrum. Wavelength sampling is
        returned separately by the calling calibration function.

    Raises:
        NoBandsAvailableError: A source has no available photometer.
        StopIteration: The parsed input contains no sources.
    """
    spectra = (_create_spectrum(row, truncation, design_matrices, merge, release,
                                with_correlation=with_correlation) for row in tqdm(
        parsed_input_data.itertuples(index=False), total=len(parsed_input_data),
        desc=pbar_message[__FUNCTION_KEY], unit=pbar_units[__FUNCTION_KEY], leave=False,
        colour=pbar_colour, disable=disable_info, file=stdout))

    return format_sampled_output(spectra, include_xp=False, with_correlation=with_correlation, with_stdev=False)


def _create_spectrum(row: dict, truncation: bool, design_matrix: dict[str, "np.ndarray"],
                     merge: dict[str, "np.ndarray"], release,
                     with_correlation: bool = False) -> CalibrationAbsoluteSampledSpectrum:
    """Calibrate one source and combine its available BP/RP contributions.

    Args:
        row (namedtuple): Source row from DataFrame.itertuples(index=False).
            Fields include source_id and each band's coefficients, covariance
            information and standard_deviation, with 'bp_' and 'rp_' prefixes.
        truncation (bool): Use this source's bp_n_relevant_bases count for BP
            and rp_n_relevant_bases count for RP. False uses all basis functions.
        design_matrix (dict[str, SampledBasisFunctions]): Per-band design matrices
            and their common wavelength grid in nm.
        merge (dict[str, numpy.ndarray]): BP/RP weights, one per wavelength sample.
        release (str): Gaia release used for wavelength limits when a band is missing.
        with_correlation (bool): Calculate sample covariance for output correlations.

    Returns:
        CalibrationAbsoluteSampledSpectrum: Calibrated fluxes and flux errors,
        with sample covariance when requested. The object handles BP/RP merging
        or masks the unsupported end of a single-band result.

    Raises:
        NoBandsAvailableError: Neither band has a covariance array available
            for calibration.
    """
    source_id = row.source_id

    continuous_dict = {band: XpContinuousSpectrum(source_id, band, getattr(row, f'{band}_coefficients'),
                                                  get_covariance_matrix(row, band),
                                                  getattr(row, f'{band}_standard_deviation')) for band in BANDS}

    recommended_truncation = {band: getattr(row, f'{band}_n_relevant_bases') for band in BANDS} if truncation else {}

    return CalibrationAbsoluteSampledSpectrum(source_id, continuous_dict, design_matrix, merge, release,
                                              truncation=recommended_truncation, with_correlation=with_correlation)
