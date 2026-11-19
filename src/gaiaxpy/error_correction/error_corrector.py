"""Select and apply magnitude-dependent factors to photometric flux errors.

Use bundled tables for the selected Gaia release. Match passbands by name,
leave unsupported systems and passbands unchanged, and record which correction
tables were actually applied. Unexpected missing passbands and missing tables
are reported on stderr, including when routine messages are disabled.
"""
from copy import deepcopy
from functools import lru_cache
from os.path import isfile
from sys import stdout
from typing import List

import numpy as np
import pandas as pd
from tqdm import tqdm

from gaiaxpy.core.input_validator import validate_explicit_save_options, validate_overwrite
from gaiaxpy.core.release_resolution import parse_release
from gaiaxpy.error_correction.metadata import append_error_correction_metadata
from gaiaxpy.photometric_system.photometric_system import PhotometricSystem
from ..core.config_dispatcher import ErrorCorrectorDispatcher
from ..core.generic_functions import _warning, cast_output, extract_systems_from_data
from ..core.generic_variables import RELEASES, pbar_message, pbar_units, pbar_colour
from ..core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from ..input_reader.input_reader import InputReader
from ..output.photometry_data import PhotometryData


def apply_error_correction(input_multi_photometry, photometric_system=None, output_path='.',
                           output_file='output_corrected_photometry', release=RELEASES.dr3,
                           output_format=None, save_file=True, *, disable_info=False,
                           overwrite="yes"):
    """Apply error correction (see Montegriffo et al., 2022, for more details).
        Infer photometric systems if not specified.

    Args:
        input_multi_photometry (pandas.DataFrame): Photometry table containing
            flux-error columns named <system_label>_flux_error_<band>, and the release's
            Gaia Vega G-magnitude column: DR3_GaiaVega_mag_G. Other columns are retained.
            Retaining the optional source_id column is recommended so corrected photometry
            can be matched to Gaia sources.
        photometric_system (PhotometricSystem, list or None): PhotometricSystem member or
            list of PhotometricSystem members to consider. None infers system labels from the
            input columns. An explicit selection must also include the release's
            Gaia Vega system, even if its column is already in the input table.
        output_path (str or pathlib.Path): Destination directory when saving;
            defaults to the current directory. Missing directories are created.
        output_file (str): Output filename stem without an extension. Defaults
            to 'output_corrected_photometry'.
        release (str or None): Gaia release. Defaults to 'dr3', the only
            supported release. The corrector does not infer the release
            from input photometry or existing output metadata.
        output_format (str or None): 'csv', 'ecsv', 'fits' or 'xml'
            (VOTable), ignoring case and an initial dot. None selects CSV.
        overwrite (str): 'yes' or 'y' replaces existing files (default: 'yes').
            'no' or 'n' raises FileExistsError if any output exists. 'ask' prompts
            once before replacing existing files. Values are case-insensitive.
            Declining skips saving. With save_file=False, 'ask' emits a warning unless disable_info=True.
        save_file (bool): Save the corrected table; defaults to True. False
            returns the result without writing files.
        disable_info (bool): Suppress routine messages and progress bars;
            defaults to False. Missing-table and missing-passband warnings
            remain visible.
        overwrite (str): 'yes' or 'y' replaces existing files (default: 'yes').
            'no' or 'n' raises FileExistsError if any output exists. 'ask' prompts
            once before replacing existing files. Values are case-insensitive.

    Returns:
        pandas.DataFrame: Prepared input photometry with supported flux-error
        columns multiplied by their correction factors. Fluxes, magnitudes and
        unsupported flux-error columns are unchanged. The supplied DataFrame
        is not modified.

    Raises:
        ValueError: Required Gaia Vega photometry is missing
            from the selection, detected system labels disagree with release,
            a magnitude cannot be assigned correction factors, or existing
            metadata is malformed.
        KeyError: A required input or correction-table field is missing.
        FileNotFoundError: An expected correction table is missing.
        InvalidReleaseError: The supplied Gaia release is unsupported.

    Notes:
        File input is not implemented; load saved photometry into a DataFrame
        before calling this function. Use uncorrected photometry as input: each call
        multiplies the errors again, even if metadata records an earlier call.

        Factors are selected by Gaia Vega G magnitude using the table's bins
        and interpolation rule. Values strictly outside the table limits use
        the nearest end row; a missing G magnitude uses the final row's factors.
        Systems and passbands without applicable tables are skipped with a warning.
    """
    overwrite = validate_overwrite(overwrite)
    release = parse_release(release)
    corrector = ErrorCorrector(release)
    return corrector.apply_correction(input_multi_photometry, photometric_system=photometric_system,
                                      output_path=output_path, output_file=output_file,
                                      output_format=output_format, save_file=save_file, record_metadata=True,
                                      disable_info=disable_info, overwrite=overwrite)


class ErrorCorrector:
    """Manage correction tables and applied-passband records for one Gaia release.

    applied_corrections records the systems, files and passbands changed during the
    latest apply_correction call. The generation pipeline can supply separate Gaia
    Vega reference photometry rather than adding reference columns to its output.
    """

    def __init__(self, release):
        """Select a Gaia release and its built-in Gaia Vega reference member.

        Args:
            release (str): 'dr3', ignoring case. Must be supplied.

        Raises:
            KeyError: release is None.
            InvalidReleaseError: The supplied release label is unsupported.

        Notes:
            Correction tables are read later, when needed.
        """
        _gaia_system_dict = {RELEASES.dr3: PhotometricSystem.DR3_Gaia_Vega}
        release = parse_release(release)
        self._release = release
        self._gaia_system = _gaia_system_dict[release]
        self._gaia_system_full_label = self._gaia_system.get_system_full_label()
        self.applied_corrections = []
        self._correction_paths = {}

    def requires_gaia_system_addition(self, _photometric_systems: List) -> bool:
        """Check whether a non-empty selection contains this release's Gaia Vega system.

        Args:
            _photometric_systems (list): Either system members exposing name and
                value, or full column-label strings such as 'DR3_GaiaVega'.
                Do not mix these representations in one list.

        Returns:
            bool: True when Gaia Vega is absent; False when present.

        Raises:
            ValueError: The selection is empty.
            TypeError: Input is not a list or contains unsupported/mixed entries.
        """

        def _is_photometric_system(x):
            # True if it's an enum member
            """Check for name and value attributes without validating registry membership."""
            return hasattr(x, 'name') and hasattr(x, 'value')

        if not _photometric_systems:
            raise ValueError('At least one system must be requested.')
        if not isinstance(_photometric_systems, list):
            raise TypeError('Photometric systems must be a list.')
        if all(_is_photometric_system(x) for x in _photometric_systems):
            return not any(system.name == self._gaia_system.name for system in _photometric_systems)
        elif all(isinstance(x, str) for x in _photometric_systems):
            return not any(system == self._gaia_system_full_label for system in _photometric_systems)
        else:
            raise TypeError(f'The value provided for _photometric_systems was not understood: {_photometric_systems}.')

    def get_required_systems(self, error_correction: bool, requires_gaia_addition: bool, phot_systems: list):
        """Return a selection copy with Gaia Vega added when this helper requires it.

        Args:
            error_correction (bool): Whether flux-error correction is requested.
            requires_gaia_addition (bool): Whether Gaia Vega is absent from the list.
            phot_systems (list): Photometric-system members.

        Returns:
            list: New list with Gaia Vega appended if it is absent and either
            error_correction is True or any base system name ends in Std. Otherwise,
            return a shallow copy of the original list.
        """
        return [*phot_systems, self._gaia_system] if (requires_gaia_addition and error_correction) else (
            phot_systems.copy())

    def get_gaia_full_label(self):
        """Return the release's Gaia Vega column label, such as DR3_GaiaVega."""
        return self._gaia_system_full_label

    def get_gaia_system(self):
        """Return the release's built-in Gaia Vega registry member."""
        return self._gaia_system

    def get_release(self):
        """Return the normalised Gaia release used by this corrector."""
        return self._release

    @lru_cache(maxsize=None)
    def get_correctable_systems(self):
        """Discover and cache the system labels with correction-table filenames.

        Returns:
            list[str]: Labels found by the release-specific configuration dispatcher.
            This discovers filenames; table contents are checked when read.
        """
        dispatcher = ErrorCorrectorDispatcher()
        return dispatcher.build_systems_names(release=self.get_release())

    @staticmethod
    def get_systems_to_correct(systems_in_data, correctable_systems):
        """Return the distinct labels shared by the input and available correction tables.

        Args:
            systems_in_data (iterable[str]): Input system labels.
            correctable_systems (iterable[str]): Labels with available tables.

        Returns:
            list[str]: Set intersection; ordering is not guaranteed.
        """
        return list(set(systems_in_data) & set(correctable_systems))

    def correct_errors(self, function_key: str, input_multi_photometry: 'pd.DataFrame', systems_to_correct: list[str],
                       gaia_reference_photometry=None, disable_info=False):
        """Update matched flux-error columns in place using Gaia G-magnitude factors.

        Args:
            function_key (str): Progress-message key, normally 'correction'.
            input_multi_photometry (pandas.DataFrame): Working photometry table to
                update. Includes this release's Gaia Vega G magnitude unless a
                separate reference is supplied.
            systems_to_correct (list[str]): System labels with correction tables.
            gaia_reference_photometry (pandas.DataFrame or None): Separate reference
                containing Gaia Vega G magnitudes in the same row order as the input.
                None selects G magnitudes from input_multi_photometry.
            disable_info (bool): Suppress the progress bar and routine messages.

        Notes:
            Factors are matched to flux-error columns by passband name, not column
            position. Only matched columns are replaced.
        """
        # Precompute system columns for efficiency
        columns = input_multi_photometry.columns
        # Ignore G mag, it's added in the loop
        system_column_masks = {system: (columns.str.startswith(system) & ~columns.str.contains(f'{system}Std'))
                               for system in systems_to_correct}
        gaia_G_mag_column = f'{self.get_gaia_full_label()}_mag_G'
        gaia_source = input_multi_photometry if gaia_reference_photometry is None else gaia_reference_photometry
        gaia_G_mag = gaia_source[gaia_G_mag_column]
        for system in tqdm(systems_to_correct, desc=pbar_message[function_key], total=len(systems_to_correct),
                           unit=pbar_units[function_key], leave=False, colour=pbar_colour, file=stdout,
                           disable=disable_info):
            mask = system_column_masks[system].copy()  # Copy existing mask
            system_df = input_multi_photometry.loc[:, mask].copy()
            # The correction factors are always selected from the explicit Gaia
            # reference photometry when one is supplied.
            correction_table = self._read_system_table(system)
            correction_array = self._get_correction_array(gaia_G_mag, system, correction_table)
            factor_columns = [col for col in correction_table.columns if col.startswith('factor_')]
            # Correct only passbands represented in the correction table.
            corrected_system = ErrorCorrector._correct_system(system_df, correction_array, factor_columns, system,
                                                              disable_info=disable_info)
            # Apply correction to the original input_multi_photometry
            input_multi_photometry.loc[:, corrected_system.columns] = corrected_system.to_numpy()
            if not corrected_system.empty and system in self._correction_paths:
                self.applied_corrections.append({
                    'system': system, 'file': self._correction_paths[system],
                    'passbands': [column.split('_flux_error_', 1)[1] for column in corrected_system.columns]})

    def _get_correction_array(self, mag_G_values: 'pd.Series', system, correction_table=None):
        """Return a float64 factor matrix in source row order and table passband order.

        Args:
            mag_G_values (pandas.Series): Reference Gaia Vega G magnitudes.
            system (str): Full system column label used to locate its table.

        Returns:
            pandas.Series: One factor array per source, preserving the magnitude
            Series index. Factor order follows the table's factor_ columns.

        Raises:
            ValueError: A magnitude inside the table range matches no bin, or the
            selected row cannot provide factors.
        """
        if correction_table is None:
            correction_table = self._read_system_table(system)
        lower = correction_table['min_Gmag_bin'].to_numpy()
        upper = correction_table['max_Gmag_bin'].to_numpy()
        centres = correction_table['bin_centre'].to_numpy()
        factor_columns = [column for column in correction_table.columns if column.startswith('factor_')]
        factors = correction_table[factor_columns].to_numpy(dtype=np.float64)
        magnitudes = mag_G_values.to_numpy(dtype=np.float64, na_value=np.nan)

        corrected_factors = np.empty((len(magnitudes), len(factor_columns)), dtype=np.float64)
        corrected_factors[:] = factors[-1]
        corrected_factors[magnitudes < lower[0]] = factors[0]

        # Sort only the in-range magnitudes so each bin can select a contiguous slice.
        in_range = np.flatnonzero((magnitudes >= lower[0]) & (magnitudes < upper[-1]))
        positions = in_range[np.argsort(magnitudes[in_range])]
        sorted_magnitudes = magnitudes[positions]
        starts = np.searchsorted(sorted_magnitudes, lower)
        stops = np.searchsorted(sorted_magnitudes, upper)
        assigned = np.zeros(len(magnitudes), dtype=bool)
        rows_by_lower_edge = {}
        for row, edge in enumerate(lower):
            rows_by_lower_edge.setdefault(edge, row)

        for row, (start, stop) in enumerate(zip(starts, stops, strict=True)):
            bin_positions = positions[start:stop]
            # If bins overlap, the first row in table order takes precedence.
            bin_positions = bin_positions[~assigned[bin_positions]]
            assigned[bin_positions] = True
            corrected_factors[bin_positions] = factors[row]
            next_row = rows_by_lower_edge.get(upper[row])
            if next_row is not None:
                interpolate = bin_positions[magnitudes[bin_positions] > centres[row]]
                slope = (factors[next_row] - factors[row]) / (upper[row] - centres[row])
                offsets = magnitudes[interpolate] - centres[row]
                corrected_factors[interpolate] = offsets[:, None] * slope + factors[row]

        unmatched = in_range[~assigned[in_range]]
        if unmatched.size:
            mag = magnitudes[unmatched[0]]
            raise ValueError(f'No row in the table matched magnitude {mag} and system {system}.')
        return corrected_factors

    @staticmethod
    def _correct_system(system_df, correction_array, factor_columns=None, system=None, *, disable_info=False):
        """Return corrected flux-error columns for passbands represented in the table.

        Args:
            system_df (pandas.DataFrame): Columns for one system. Error fields must
                follow <system_label>_flux_error_<band>.
            correction_array (numpy.ndarray): Factor matrix in the same row order
                as system_df.
            factor_columns (list[str] or None): Table column names, factor_<band>,
                defining factor-vector order. None derives names from error columns.
            system (str or None): System label used in missing-passband messages.
            disable_info (bool): Suppress information messages.

        Returns:
            pandas.DataFrame: Multiplied flux-error columns in table passband order,
            with the original index. No matches returns a column-free DataFrame.
        """
        error_df = system_df.filter(like='_error_', axis=1)
        if factor_columns is None:
            factor_columns = [f"factor_{column.rsplit('_', 1)[-1]}" for column in error_df.columns]

        factor_bands = [column.removeprefix('factor_') for column in factor_columns]
        error_columns_by_band = {column.split('_flux_error_', 1)[1]: column for column in error_df.columns}
        missing_bands = [band for band in error_columns_by_band if band not in factor_bands]
        if missing_bands:
            ErrorCorrector.warn_missing_band(missing_bands, system)

        matched_bands = [band for band in factor_bands if band in error_columns_by_band]
        matched_error_columns = [error_columns_by_band[band] for band in matched_bands]
        if not matched_error_columns:
            return pd.DataFrame(index=system_df.index)

        factor_indices = [factor_bands.index(band) for band in matched_bands]
        product_array = error_df.loc[:, matched_error_columns].to_numpy() * correction_array[:, factor_indices]
        return pd.DataFrame(product_array, index=system_df.index, columns=matched_error_columns)

    @staticmethod
    def warn_missing_band(missing_bands: list, system):
        """Print a stderr warning that the listed passbands' flux errors are unchanged."""
        if len(missing_bands) == 1:
            message = (f'The {missing_bands[0]} passband is missing from the {system} correction table file. '
                       'The errors associated with this band will not be corrected.')
        else:
            bands = ', '.join(missing_bands)
            message = (f'The {bands} passbands are missing from the {system} correction table file. '
                       f'The associated errors will not be corrected.')
        _warning(message)

    def _read_system_table(self, system):
        """Read a system's correction CSV and calculate the magnitude-bin centres.

        Args:
            system (str): Full column label used by the configuration dispatcher.

        Returns:
            pandas.DataFrame: Parsed table with an added bin_centre column, equal
            to the midpoint of min_Gmag_bin and max_Gmag_bin.

        Raises:
            FileNotFoundError: The resolved correction table is absent.
        """
        dispatcher = ErrorCorrectorDispatcher()
        correction_factors_path = dispatcher.build_system(self.get_release(), system)
        if isfile(correction_factors_path):
            correction_table = pd.read_csv(correction_factors_path, comment='#', **CSV_FLOAT_PRECISION_KWARGS)
            correction_table['bin_centre'] = (correction_table['min_Gmag_bin'] + correction_table['max_Gmag_bin']) / 2
            self._correction_paths[system] = correction_factors_path
            return correction_table
        raise FileNotFoundError(f'No correction table found for system {system}.')

    def apply_correction(self, input_multi_photometry, photometric_system=None, output_path='.',
                         output_file='output_corrected_photometry', output_format=None, save_file=True,
                         disable_info=False, gaia_reference_photometry=None, *, record_metadata=False, overwrite="yes"):
        """Read photometry, correct supported flux errors and optionally save the result.

        Args:
            input_multi_photometry (pandas.DataFrame): Photometry table, as described
                by apply_error_correction. File input is not implemented.
            photometric_system (PhotometricSystem, list or None): Selection to
                consider; None infers labels from input columns.
            output_path (str or pathlib.Path): Destination directory; defaults to '.'.
            output_file (str): Filename stem; defaults to 'output_corrected_photometry'.
            output_format (str or None): Output format, or None for CSV.
            save_file (bool): Write the result; defaults to True.
            disable_info (bool): Suppress routine messages and progress bars.
            gaia_reference_photometry (pandas.DataFrame or None): Internal reference
                table with this release's Gaia Vega G-magnitude column in matching
                row order. When supplied, Gaia Vega need not appear in the selected
                output systems or input table. None requires it in the input selection.
            record_metadata (bool): Append an operation-history record; defaults
                to False. The public function enables this, while generate records
                correction provenance in its own output metadata.

        Returns:
            pandas.DataFrame: Prepared photometry with supported flux errors
            corrected. The caller's input DataFrame is not modified.
        """
        overwrite = validate_overwrite(overwrite)
        validate_explicit_save_options(save_file, output_file, output_format)
        __FUNCTION_KEY = 'correction'
        self.applied_corrections = []
        self._correction_paths = {}
        # The correction can only be applied for the systems present in the config files
        __correctable_systems = self.get_correctable_systems()
        input_multi_photometry, extension, release = InputReader(input_multi_photometry, apply_error_correction,
                                                                 truncation=False, disable_info=disable_info).read()
        systems_in_data = extract_systems_from_data(input_multi_photometry, release=self.get_release(),
                                                    photometric_system=photometric_system)
        # Gaia may either be present in the input itself (public API behaviour)
        # or be supplied explicitly by the generator as reference photometry.
        if gaia_reference_photometry is None:
            self.check_gaia_is_present(systems_in_data)
        # Only correct the systems that can be corrected
        systems_to_correct = self.get_systems_to_correct(systems_in_data, __correctable_systems)
        ErrorCorrector.display_skipped_systems(systems_in_data, __correctable_systems, disable_info)
        input_multi_photometry.attrs = deepcopy(input_multi_photometry.attrs)
        # Correct errors in DataFrame (in-place operation)
        self.correct_errors(__FUNCTION_KEY, input_multi_photometry, systems_to_correct,
                            gaia_reference_photometry=gaia_reference_photometry, disable_info=disable_info)
        if record_metadata:
            append_error_correction_metadata(input_multi_photometry, self)
        # Format output data
        output_data = PhotometryData(input_multi_photometry)
        output_data.data = cast_output(output_data)
        output_data.save(save_file, output_path, output_file, output_format, extension, disable_info=disable_info,
                         overwrite=overwrite)
        return input_multi_photometry

    def check_gaia_is_present(self, systems_in_data: list[str]):
        """Raise ValueError if the supplied selection lacks this release's Gaia Vega label."""
        if self.requires_gaia_system_addition(systems_in_data):
            raise ValueError(f'System {self.get_gaia_full_label()}, required to apply the error correction is not '
                             f'present in the input photometry.')

    @staticmethod
    def display_skipped_systems(systems_in_data, correctable_systems, disable_info):
        """Warn about every input system without a correction table.

        Args:
            systems_in_data (iterable[str]): Input system labels.
            correctable_systems (iterable[str]): Labels with correction tables.
            disable_info (bool): Suppress the leading blank line only; warnings
                are always printed to stderr.
        """
        systems_to_skip = set(systems_in_data) - set(correctable_systems)
        if systems_to_skip and not disable_info:
            print()
        for system in systems_to_skip:
            _warning(f'System {system} does not have a correction table. The program will not apply error correction '
                     f'over this system.')

    def format_error_output(self, photometry_df, required_gaia_addition):
        """Remove internally added Gaia Vega columns when requested.

        Args:
            photometry_df (pandas.DataFrame): Photometry result.
            required_gaia_addition (bool): Whether to drop columns starting with
                this corrector's Gaia Vega label.

        Returns:
            pandas.DataFrame: Table with reference columns dropped when True;
            otherwise the supplied object. Does not modify the supplied table.
        """
        if required_gaia_addition:  # Remove Gaia Vega system from the final result
            gaia_columns = [column for column in photometry_df if column.startswith(self.get_gaia_full_label())]
            photometry_df = photometry_df.drop(columns=gaia_columns)
        return photometry_df
