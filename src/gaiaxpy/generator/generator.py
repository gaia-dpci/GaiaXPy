"""Coordinate synthetic photometry generation, corrections and output metadata.

Read continuous BP/RP spectra, evaluate the requested systems and apply their
configured standardisation. Optional flux-error correction uses separately
prepared Gaia Vega reference photometry.
Return the requested photometry and save it when requested.
"""
from pathlib import Path
from typing import Union, Optional

from gaiaxpy.colour_equation.xp_filter_system_colour_equation import _apply_colour_equation
from gaiaxpy.core.generic_functions import format_additional_columns, validate_photometric_system
from gaiaxpy.core.output_metadata import OUTPUT_METADATA_KEY
from gaiaxpy.core.release_resolution import parse_release, check_release_matches_data
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.output.photometry_data import PhotometryData
from .metadata import build_generator_metadata
from .multi_synthetic_photometry_generator import MultiSyntheticPhotometryGenerator
from ..core.input_validator import validate_save_arguments, validate_overwrite
from ..error_correction.error_corrector import ErrorCorrector
from ..file_parser.cast import _cast


def generate(input_object: Union[list, Path, 'pd.DataFrame', 'pd.Series', str],
             photometric_system: Union[list, 'PhotometricSystem'], truncation: bool = False,
             output_path: Union[Path, str] = '.', output_file: str = 'output_synthetic_photometry',
             output_format: str = None, save_file: bool = True, error_correction: bool = False,
             additional_columns: Optional[Union[dict, list, str]] = None, username: str = None, password: str = None,
             credentials_file: str | Path = None, release: str | None = None, *, disable_info: bool = False,
             overwrite="yes") -> 'pd.DataFrame':
    """Generate magnitudes, fluxes and flux errors in selected photometric systems.

    Args:
        input_object (str, pathlib.Path, pandas.DataFrame, pandas.Series, list or tuple): Input
            continuous BP/RP mean spectra. Supply a local file, a DataFrame, a single spectrum
            row as a Series, a list or tuple of source IDs supplied as integers or integer
            strings, or an ADQL query. Files can use CSV, ECSV, FITS or XML/VOTable, including
            supported gzip inputs and Archive ZIP files. Source-ID lists and tuples, and queries
            retrieve Archive data.
        photometric_system (PhotometricSystem or list): Current registry member
            or non-empty list of members, all for the same Gaia release.
            Additional members include their version, for example
            PhotometricSystem.USER_DR3_Example_v1. Removed or replaced additional
            members must be selected again from the current registry.
        truncation (bool): Use the recommended number of basis functions for
            each source and photometer. True uses bp_n_relevant_bases for BP
            and rp_n_relevant_bases for RP, taking the counts from each input
            row. False, the default, uses all available basis functions.
            Non-positive counts leave that photometer untruncated.
        output_path (str or pathlib.Path): Destination directory when saving;
            defaults to the current directory. Missing directories are created.
        output_file (str): Output filename stem without an extension. Defaults
            to 'output_synthetic_photometry'.
        output_format (str or None): 'csv', 'ecsv', 'fits' or 'xml'
            (VOTable), ignoring case and an initial dot. None uses the underlying
            input format; for example, .csv.gz selects CSV output. DataFrame
            and Archive inputs default to CSV.
        overwrite (str): 'yes' or 'y' replaces existing files (default: 'yes').
            'no' or 'n' raises FileExistsError if any output exists. 'ask' prompts
            once before replacing existing files. Values are case-insensitive.
            Declining skips saving. With save_file=False, 'ask' emits a warning unless disable_info=True.
        save_file (bool): Save the result; defaults to True. False returns the
            DataFrame without writing files. Supplying output_file or
            output_format when saving is disabled may produce a warning.
        error_correction (bool): Apply tabulated correction factors to flux errors
            for supported systems and passbands. Defaults to False. Fluxes and
            magnitudes are not changed by this step. Availability and applied
            correction files are recorded in the result metadata.
        additional_columns (str, list, dict or None): Extra input columns to keep
            in the result, such as ['bp_chi_squared', 'rp_chi_squared']. A dictionary
            maps output names to input names, for example {'bp_nt': 'bp_n_transits'}.
            Columns must already be present in the input table or returned Archive
            product. Required and optional spectrum-column names cannot be overwritten.
        username (str or None): Cosmos username for Archive access.
        password (str or None): Cosmos password, supplied with username when
            authenticating through these arguments.
        credentials_file (str or pathlib.Path or None): UTF-8 credentials file
            with username and password on separate lines. Cannot be combined
            with username or password. Without supplied credentials, the Archive
            reader may request an interactive login when authentication is needed.
        release (str or None): Gaia release. Defaults to 'dr3'. When identifiable,
            the input release and photometric systems must match the selected release.
        disable_info (bool): Suppress routine messages and progress bars;
            defaults to False. Warnings, errors and required login prompts
            remain visible.

    Returns:
        pandas.DataFrame: One row per input source, containing source_id and
        <system_label>_mag_<band>, <system_label>_flux_<band> and
        <system_label>_flux_error_<band> columns for each selected system.
        Additional-system labels include USER, release, name and version, so
        different versions produce distinct columns. Requested extra
        input columns are retained when they do not duplicate generated columns.

        attrs['gaiaxpy_metadata'] records the GaiaXPy package version separately
        from filter versions, plus configuration files and corrections used.
        Additional-filter records include file identity and associated columns.

    Raises:
        TypeError: The selection contains a string or another value that is not a
            PhotometricSystem member.
        ValueError: The system selection is empty, inactive or mixes releases;
            input and system releases disagree; or required input or filter
            configuration values are invalid.

    Notes:
        System standardisation is applied automatically, independently of
        error_correction. This includes applicable DR3 colour equations.
        Required Gaia Vega reference photometry is computed internally; it is
        not added to the returned columns unless requested as an output system.
        Missing BP or RP spectra give NaN photometry. Non-positive flux gives
        a NaN magnitude.

        Metadata is prepared even when saving is disabled. CSV writes an ordinary
        table plus <output_file>_metadata.csv; other supported formats embed the
        metadata. File-reading, Archive and output-writing errors are reported
        to the caller.
    """
    overwrite = validate_overwrite(overwrite)
    return _generate(input_object=input_object, photometric_system=photometric_system, truncation=truncation,
                     output_path=output_path, output_file=output_file, output_format=output_format, save_file=save_file,
                     error_correction=error_correction, additional_columns=additional_columns, username=username,
                     password=password, credentials_file=credentials_file, release=release, disable_info=disable_info,
                     overwrite=overwrite)


def _generate(input_object: Union[list, Path, 'pd.DataFrame', 'pd.Series', str],
              photometric_system: Union[list, 'PhotometricSystem'], *, truncation: bool = False,
              output_path: Union[Path, str] = '.', output_file: str = 'output_synthetic_photometry',
              output_format: str = None, save_file: bool = True, error_correction: bool = False,
              additional_columns: Optional[Union[dict, list, str]] = None, selector=None, username: str = None,
              password: str = None, credentials_file: str | Path = None, release=None, disable_info: bool = False,
              overwrite="yes") -> 'pd.DataFrame':
    """Run the generation pipeline with internal configuration options.

    Arguments, results and input requirements are described by generate. Systems
    are validated before input is read. After passband integration, apply colour
    equations and optional flux-error correction in that order, then attach extra
    input columns and output metadata.

    Args:
        selector (callable or None): Internal selection argument forwarded to
            InputReader. Leave as None for ordinary use; readers that do not
            support selectors reject a supplied value.

    Returns:
        pandas.DataFrame: Requested photometry with output metadata.
    """
    overwrite = validate_overwrite(overwrite)
    photometric_system = validate_photometric_system(photometric_system)
    release = parse_release(release)
    validate_save_arguments(generate.__defaults__[2], output_file, generate.__defaults__[3], output_format, save_file)
    # Parse additional columns
    additional_columns = format_additional_columns(additional_columns)
    if release is not None:
        first_system = photometric_system[0] if isinstance(photometric_system, list) else photometric_system
        system_release = first_system.value.get_release()
        if release != system_release:
            raise ValueError(f"The supplied release '{release}' does not match the selected photometric "
                             f"systems' release '{system_release}'.")
    # Read input data
    reader = InputReader(input_object, generate, truncation=truncation, additional_columns=additional_columns,
                         selector=selector, disable_info=disable_info, user=username, password=password,
                         release=release, credentials_file=credentials_file)
    parsed_input_data, extension, release = reader.read()
    additional_data = parsed_input_data[list(additional_columns.keys())]
    release = check_release_matches_data(photometric_system, parsed_input_data, generate.__name__, release=release)
    requested_systems = photometric_system

    # Generate only the requested photometry.
    phot_generator = MultiSyntheticPhotometryGenerator(requested_systems)
    photometry_df = phot_generator.generate(parsed_input_data, truncation=truncation, disable_info=disable_info)
    standardisations = list(phot_generator.standardisations)
    photometry_df = _apply_colour_equation(photometry_df, photometric_system=requested_systems, save_file=False,
                                           disable_info=True, metadata_records=standardisations)

    _err_corr = ErrorCorrector(release)
    needs_gaia_reference = error_correction
    gaia_reference_df = None
    reference_files = []
    if needs_gaia_reference:
        gaia_system = _err_corr.get_gaia_system()
        gaia_reference_system = gaia_system
        requested_gaia_200 = any(system.name == gaia_system.name for system in requested_systems)

        if requested_gaia_200:
            # The requested Gaia photometry is already exactly the required reference.
            gaia_reference_df = photometry_df
            reference_files = [(system, path) for system, path in phot_generator.system_files
                               if system.name == gaia_system.name]
        else:
            gaia_generator = MultiSyntheticPhotometryGenerator([gaia_reference_system])
            gaia_reference_df = gaia_generator.generate(parsed_input_data, truncation=truncation,
                                                        disable_info=True)
            reference_files = gaia_generator.system_files

    if error_correction:
        photometry_df = _err_corr.apply_correction(photometry_df, photometric_system=requested_systems,
                                                   gaia_reference_photometry=gaia_reference_df,
                                                   save_file=False, disable_info=disable_info)
    photometry_columns = list(photometry_df.columns)
    additional_data = additional_data[[c for c in additional_data.columns if c not in photometry_df.columns]]

    from pandas import concat as pd_concat
    photometry_df = pd_concat([photometry_df, additional_data], axis=1)
    photometry_df = _cast(photometry_df)
    photometry_df.attrs[OUTPUT_METADATA_KEY] = build_generator_metadata(
        release, reader, phot_generator.system_files, reference_files, standardisations, _err_corr, error_correction,
        columns=photometry_columns)
    # Save data
    output_data = PhotometryData(photometry_df)

    output_data.save(save_file, output_path, output_file, output_format, extension, disable_info=disable_info,
                     overwrite=overwrite)
    return _cast(photometry_df)
