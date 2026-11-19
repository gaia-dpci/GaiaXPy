"""Synthetic photometry in multiple photometric systems."""
import re
from typing import List


def _flatten_list(lst):
    """Flatten one level of nested values, retaining their order.

    Args:
        lst (iterable): Sublists or other iterable groups.

    Returns:
        list: Items in group order.
    """
    return [item for sublist in lst for item in sublist]


def _generate_variables(photometries):
    # A photometry corresponds to the photometry of a single source id in all the different systems
    """Collect magnitudes, fluxes and errors in source/system/passband order.

    Args:
        photometries (list[list[SingleSyntheticPhotometry]]): One group per
            source, with one photometry object per selected system.

    Returns:
        tuple: Nested magnitude, flux and flux-error lists, in that order.
    """
    mags = [[photometry.mag for photometry in multi_photometry] for multi_photometry in photometries]
    fluxes = [[photometry.flux for photometry in multi_photometry] for multi_photometry in photometries]
    flux_errors = [[photometry.flux_error for photometry in multi_photometry] for multi_photometry in photometries]
    return mags, fluxes, flux_errors


def _get_source_ids(photometries):
    """Take the source identifier from the first system result in each group.

    Args:
        photometries (list[list[SingleSyntheticPhotometry]]): Non-empty system
            groups, one per source.

    Returns:
        list: Source identifiers in input order.

    Raises:
        IndexError: A source has an empty system group.
    """
    return [photometry[0].source_id for photometry in photometries]


class MultiSyntheticPhotometry:
    """Synthetic photometry derived from Gaia spectra in multiple photometric systems.

    The selected systems and each source's photometry objects must have the same
    order. Additional-system labels retain their version in every column name.
    """

    def __init__(self, photometric_system, photometries):
        """Store system selections and collect the corresponding source results.

        Args:
            photometric_system (list[PhotometricSystem]): Selected systems in output
                order. Each provides its prefix, system label and passband names.
            photometries (list[list[SingleSyntheticPhotometry]]): One list per
                source, containing one result per system in the same order.

        Notes:
            Input alignment and passband counts are assumed rather than validated.
            Every source group must contain at least one result.
        """
        self.photometric_system = photometric_system
        # One element per source_id, each sub element corresponds to one photometric_system
        self.photometries = photometries
        self.source_ids = _get_source_ids(photometries)
        self.mags, self.fluxes, self.errors = _generate_variables(photometries)
        self.system_bands_tuples = [(f'{phot_system.value.get_system_prefix()}_{phot_system.get_system_label()}',
                                     phot_system.get_bands()) for phot_system in self.photometric_system]

    def generate_output_df(self):
        """Build a photometry table grouped by the requested system order.

        Returns:
            pandas.DataFrame: One row per source, starting with source_id.
            Columns follow PREFIX_SYSTEM_mag_BAND, PREFIX_SYSTEM_flux_BAND and
            PREFIX_SYSTEM_flux_error_BAND, for magnitudes, fluxes and flux errors.
            Additional-system labels include their version. Within each system,
            values appear in magnitude, flux, flux-error order.

        Notes:
            This method assembles values and column names; operation-level metadata
            and output-file writing are handled by the calling generator.
        """

        def __get_column_sublist(_label: str, _df: 'pd.DataFrame') -> List:
            """Select columns matching a system label and a recognised value prefix.

            Args:
                _label (str): System prefix and label, used directly in a regular expression.
                _df (pandas.DataFrame): Photometry table to inspect.

            Returns:
                list[str]: Matching column names in their existing order.
            """
            _pattern = fr'{_label}_(flux_error|flux|mag)_[A-Za-z0-9]+'
            return list(filter(lambda col: re.match(_pattern, col), _df.columns))

        photometries_df = self._photometries_to_df()
        # Reorder DataFrame columns
        phot_system_labels = (f'{phot_system.value.get_system_prefix()}_{phot_system.get_system_label()}' for
                              phot_system in self.photometric_system)
        reordered_columns = ['source_id'] + [col for label in phot_system_labels for col in __get_column_sublist(
            label, photometries_df)]
        photometries_df = photometries_df[reordered_columns]
        return photometries_df

    def _photometries_to_df(self):
        """Build source rows with magnitude, flux and flux error fields.

        Returns:
            pandas.DataFrame: Table before grouping its columns by selected system.
        """
        from pandas import DataFrame as pdDf

        rows = []
        for source_id, mags, fluxes, errors in zip(
                self.source_ids, self.mags, self.fluxes, self.errors):
            row = {"source_id": source_id}
            row.update(self._field_to_dict(mags, "mag"))
            row.update(self._field_to_dict(fluxes, "flux"))
            row.update(self._field_to_dict(errors, "flux_error"))
            rows.append(row)

        return pdDf(rows)

    def _field_to_dict(self, values, name):
        """Associate one source's passband values with system-specific field names.

        Args:
            values (iterable): One value sequence per selected system, in matching
                passband order.
            name (str): Field label, normally mag, flux or flux_error.

        Returns:
            dict: PREFIX_SYSTEM_FIELD_BAND names mapped to values. Prefixes and
            labels come from the selected systems, including additional versions.

        Notes:
            Values are paired with names using zip; mismatched counts are not
            rejected, and duplicate names would overwrite earlier entries.
        """
        values = _flatten_list(values)
        # Keys generator
        keys = (f'{system}_{name}_{band}' for system, bands in self.system_bands_tuples for band in bands)

        return dict(zip(keys, values))
