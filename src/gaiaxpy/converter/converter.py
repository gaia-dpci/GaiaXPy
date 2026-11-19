"""Evaluate internally calibrated BP/RP mean spectra on a pseudo-wavelength grid.

The converter reads continuous coefficients, and validates their Gaia release.
BP and RP remain separate; flux and flux-error arrays use electrons per second.
Output includes correlations between samples when requested.
"""
from itertools import chain
from pathlib import Path
from sys import stdout
from typing import Union, Optional, Tuple

import numpy as np
from tqdm import tqdm

from gaiaxpy.core.generic_functions import cast_output, validate_pwl_sampling, format_sampled_output, parse_config
from gaiaxpy.core.generic_variables import pbar_colour, pbar_units, pbar_message
from gaiaxpy.core.output_metadata import OUTPUT_METADATA_KEY, collect_output_metadata
from gaiaxpy.core.release_resolution import parse_release
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.output.sampled_spectra_data import SampledSpectraData
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum
from gaiaxpy.spectrum.xp_sampled_spectrum import XpSampledSpectrum
from .config import get_transposed_design_matrices
from ..core.config_dispatcher import ConverterDispatcher
from ..core.input_validator import validate_save_arguments, validate_overwrite

__FUNCTION_KEY = 'converter'


def convert(input_object: Union[list, tuple, Path, "pd.DataFrame", "pd.Series", str],
            sampling: Optional[np.ndarray] = np.linspace(0, 60, 600), truncation: bool = False,
            with_correlation: bool = False, output_path: Union[Path, str] = '.',
            output_file: str = 'output_spectra', output_format: str = None, save_file: bool = True,
            username: str = None, password: str = None, credentials_file: str | Path = None,
            release: str | None = None, *, disable_info: bool = False, overwrite="yes") -> Tuple[
    'pd.DataFrame', np.ndarray]:
    """Evaluate continuous BP/RP mean spectra on a pseudo-wavelength grid.

    Args:
        input_object (str, pathlib.Path, pandas.DataFrame, pandas.Series, list or tuple): Input
            continuous spectra. Supply a local file, a DataFrame,
            a single spectrum row as a Series, a list or tuple
            of source IDs supplied as integers or integer strings, or an ADQL query.
            Supported file formats are
            CSV, ECSV, FITS and XML/VOTable, including supported gzip
            inputs and Archive ZIP files. Source-ID selections and queries
            retrieve spectra from the Archive.
        sampling (numpy.ndarray): Non-empty, one-dimensional array of sorted
            pseudo-wavelength positions in the inclusive range [-10, 70]. The
            default is 600 evenly spaced positions from 0 to 60, including both
            endpoints. Passing None does not select a default grid.
        truncation (bool): Use the recommended number of basis functions for
            each source and photometer. When True, retain bp_n_relevant_bases
            functions for BP and rp_n_relevant_bases for RP, using the counts
            in that source's input row. When False, use all available basis
            functions. Non-positive counts leave that photometer untruncated.
        with_correlation (bool): Add correlations between samples and the input
            solution's standard_deviation value to each output row.
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
        save_file (bool): Write the results and sampling to disk. False returns
            them without writing; supplying output_file or output_format in
            that case may produce a warning.
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
        tuple[pandas.DataFrame, numpy.ndarray]: Sampled spectra and their shared
        pseudo-wavelength grid. The table contains source_id, xp ('BP' or 'RP'),
        flux and flux_error. Each source has a BP row followed by an RP row;
        flux and flux-error cells are missing for an unavailable photometer.
        With with_correlation=True, correlation contains the packed lower
        triangle of the sample correlation matrix, excluding its diagonal,
        and standard_deviation contains the input solution value. The data_type
        attr identifies the spectrum representation. The gaiaxpy_metadata attr
        records the release, basis configuration, package version and input
        correction status.

    Raises:
        TypeError: sampling is not a NumPy array, or a source-ID selection contains invalid types.
        ValueError: The sampling is empty, unsorted or outside the supported
            range; the input release disagrees
            with the requested release; or coefficient and basis dimensions differ.
        InvalidReleaseError: A supplied release label is not recognised.
        FileNotFoundError: A supplied local filename does not exist.

    Notes:
        BP and RP are evaluated separately on the same grid. Output positions
        remain pseudo-wavelengths, and flux and flux error remain in electron/s.
        Avro input and output are also available for internal use. The Gaia Archive
        does not distribute Avro files.

        CSV saving writes <output_file>.csv, <output_file>_sampling.csv and
        <output_file>_metadata.csv. ECSV, FITS and XML/VOTable embed
        the sampling and metadata in the main output. Existing output files
        are overwritten by default. Input-reading, Archive-access and file-writing errors
        are reported to the caller by the relevant reader or writer.
    """
    overwrite = validate_overwrite(overwrite)
    return _convert(input_object=input_object, sampling=sampling, truncation=truncation,
                    with_correlation=with_correlation, output_path=output_path,
                    output_file=output_file, output_format=output_format, save_file=save_file, username=username,
                    password=password, credentials_file=credentials_file, release=release,
                    disable_info=disable_info, overwrite=overwrite)


def _convert(input_object: Union[list, Path, str], sampling: np.ndarray = np.linspace(0, 60, 600),
             truncation: bool = False, with_correlation: bool = False,
             output_path: Union[Path, str] = '.', output_file: str = 'output_spectra', output_format: str = None,
             save_file: bool = True, username: str = None, password: str = None, credentials_file: str | Path = None,
             disable_info: bool = False,
             config_file=None, release=None, *, overwrite="yes") -> Tuple['pd.DataFrame', 'np.ndarray']:
    """Read, sample and optionally save internally calibrated BP/RP mean spectra.

    Input, sampling, truncation, correction, correlation, Archive and output
    arguments have the same meanings as in convert.

    Args:
        config_file (str or pathlib.Path or None): Internal override for the basis
            configuration. None selects the configuration for the resolved release
            through ConverterDispatcher. An override must match the input coefficients.
        release (str or None): Gaia release, resolved through InputReader using
            the same rules as convert.
        disable_info (bool): Suppress routine reading, progress and saving messages.

    Returns:
        tuple[pandas.DataFrame, numpy.ndarray]: Sampled BP/RP rows with output
        metadata attached, and the supplied pseudo-wavelength grid.
    """
    overwrite = validate_overwrite(overwrite)
    function = convert
    release = parse_release(release)
    validate_pwl_sampling(sampling)
    validate_save_arguments(function.__defaults__[4], output_file, function.__defaults__[5], output_format, save_file)
    reader = InputReader(input_object, convert, truncation=truncation, disable_info=disable_info, user=username,
                         password=password, release=release, credentials_file=credentials_file)
    parsed_input_data, extension, release = reader.read()
    if config_file is None:
        config_file = ConverterDispatcher().build(parsed_input_data=parsed_input_data, release=release)
    bases_config = parse_config(config_file)

    design_matrices = get_transposed_design_matrices(sampling, bases_config)
    spectra_df = _create_spectra(parsed_input_data, truncation, design_matrices,
                                 with_correlation=with_correlation, disable_info=disable_info)
    # Save output section
    output_data = SampledSpectraData(spectra_df, sampling)
    output_data.data = cast_output(output_data)
    output_data.data.attrs[OUTPUT_METADATA_KEY] = collect_output_metadata('convert', release, config_file,
                                                                          reader.applied_correction_files)
    output_data.save(save_file, output_path, output_file, output_format, extension, disable_info=disable_info,
                     overwrite=overwrite)
    return output_data.data, sampling


def _create_spectrum(row: 'pd.Series', truncation: bool, design_matrices: dict, band: str,
                     with_correlation: bool = False) -> XpSampledSpectrum:
    """Create a single sampled spectrum from the input continuously-represented
    mean spectrum and design matrix.

    Args:
        row (namedtuple): Source row from DataFrame.itertuples(index=False), with
            source_id and the selected band's coefficients, covariance_matrix
            and standard_deviation fields. Band fields use the 'bp_' or 'rp_' prefix.
        truncation (bool): Use this source's bp_n_relevant_bases count for BP or
            rp_n_relevant_bases count for RP. When False, retain all basis functions.
        design_matrices (dict[str, SampledBasisFunctions]): Evaluated bases and
            sampling grids keyed by 'bp' and 'rp'. Matrices have one row per
            basis function and one column per sample.
        band (str): Lowercase 'bp' or 'rp'.
        with_correlation (bool): Retain sample covariance for generating correlations.

    Returns:
        XpSampledSpectrum: Fluxes and flux errors, with optional covariance and
        the solution standard deviation. Empty coefficients give a spectrum
        containing only the source ID, photometer and sampling positions.
    """
    recommended_truncation = getattr(row, f'{band}_n_relevant_bases') if truncation else -1
    continuous_spectrum = XpContinuousSpectrum(getattr(row, 'source_id'), band,
                                               getattr(row, f'{band}_coefficients'),
                                               getattr(row, f'{band}_covariance_matrix'),
                                               getattr(row, f'{band}_standard_deviation'))

    return XpSampledSpectrum.from_continuous(continuous_spectrum, design_matrices.get(band),
                                             truncation=recommended_truncation, with_correlation=with_correlation)


def _create_spectra(parsed_input_data: 'pd.DataFrame', truncation: bool, design_matrices: dict,
                    with_correlation: bool = False, disable_info=False) -> 'pd.DataFrame':
    """Create sampled BP and RP output rows for every parsed source.

    Args:
        parsed_input_data (pandas.DataFrame): Normalised continuous-spectrum input.
            Required fields include source_id and each band's coefficients,
            covariance_matrix and standard_deviation; truncation also uses
            bp_n_relevant_bases and rp_n_relevant_bases.
        truncation (bool): Use the recommended basis count from each source's
            bp_n_relevant_bases and rp_n_relevant_bases fields. False uses all
            available basis functions.
        design_matrices (dict[str, SampledBasisFunctions]): Per-band evaluated
            bases using a common pseudo-wavelength grid.
        with_correlation (bool): Add packed sample correlations and the input
            standard_deviation to the output.
        disable_info (bool): Suppress the conversion progress bar.

    Returns:
        pandas.DataFrame: source_id, xp, flux and flux_error columns, with
        correlation and standard_deviation when requested. Input source order
        is retained, with BP before RP for each source. Missing photometer data
        retain their output row. The data_type attr identifies XpSampledSpectrum.

    Raises:
        StopIteration: The parsed input contains no sources.

    Notes:
        This helper creates the table only. The calling conversion function attaches
        processing metadata and returns the sampling separately.
    """

    def create_xp_spectra(row: 'pd.Series', _truncation: bool, _design_matrices: dict,
                          _with_correlation: bool = False) -> tuple:
        """Create the BP and RP sampled-spectrum objects for one source.

        Args:
            row (namedtuple): Normalised source row with attribute-accessible fields.
            _truncation (bool): Use the source's bp_n_relevant_bases count for BP and
                rp_n_relevant_bases count for RP; False uses all basis functions.
            _design_matrices (dict[str, SampledBasisFunctions]): Evaluated bases keyed
                by photometer.
            _with_correlation (bool): Calculate the covariance needed for output correlations.

        Returns:
            tuple[XpSampledSpectrum, XpSampledSpectrum]: BP spectrum followed by RP,
            including an object for a photometer whose coefficients are missing.
        """
        return (_create_spectrum(row, _truncation, _design_matrices, BANDS.bp, with_correlation=_with_correlation),
                _create_spectrum(row, _truncation, _design_matrices, BANDS.rp, with_correlation=_with_correlation))

    spectra = chain.from_iterable(create_xp_spectra(row, truncation, design_matrices, with_correlation)
                                  for row in tqdm(parsed_input_data.itertuples(index=False),
                                                  total=len(parsed_input_data), desc=pbar_message[__FUNCTION_KEY],
                                                  unit=pbar_units[__FUNCTION_KEY], leave=False, colour=pbar_colour,
                                                  disable=disable_info, file=stdout))

    return format_sampled_output(spectra, include_xp=True, with_correlation=with_correlation,
                                 with_stdev=with_correlation)
