"""
multi_synthetic_photometry.py
====================================
Module to represent a synthetic photometry in multiple photometric systems.
"""

import pandas as pd


def _flatten_list(lst):
    return [item for sublist in lst for item in sublist]


def _generate_variables(photometries):
    # A photometry corresponds to the photometry of a single source id in all the different systems
    mags = [[photometry.mag for photometry in multi_photometry] for multi_photometry in photometries]
    fluxes = [[photometry.flux for photometry in multi_photometry] for multi_photometry in photometries]
    flux_errors = [[photometry.error for photometry in multi_photometry] for multi_photometry in photometries]
    return mags, fluxes, flux_errors


def _get_source_ids(photometries):
    return [photometry[0].source_id for photometry in photometries]


class MultiSyntheticPhotometry(object):
    """
    Synthetic photometry derived from Gaia spectra in multiple photometric systems.
    """

    def __init__(
            self,
            photometric_system,
            photometries
            ):
        """
        Initialise a synthetic photometry in multiple photometric systems.

        TODO: add args.
        """
        self.photometric_system = photometric_system
        # One element per source_id, each subelement corresponds to one photometric_system
        self.photometries = photometries
        self.source_ids = _get_source_ids(photometries)
        self.mags, self.fluxes, self.errors = _generate_variables(photometries)

    def _generate_output_df(self):
        photometries_df = self._photometries_to_dict()
        # Reorder DataFrame columns
        phot_system_labels = [phot_system.get_system_label() for phot_system in self.photometric_system]
        reordered_columns = ['source_id']
        for label in phot_system_labels:
            column_sublist = [column for column in photometries_df.columns if column.startswith(f'{label}_')]
            reordered_columns.extend(column_sublist)
        photometries_df = photometries_df[reordered_columns]
        return photometries_df

    def _photometries_to_dict(self):
        list_of_dicts = []
        for source_id, mags, fluxes, errors in zip(self.source_ids, self.mags, self.fluxes, self.errors):
            phot = {'source_id': source_id}
            mag = self._field_to_dict(mags, 'mag')
            flux = self._field_to_dict(fluxes, 'flux')
            error = self._field_to_dict(errors, 'flux_error')
            list_of_dicts.append({**phot, **mag, **flux, **error})
        return pd.DataFrame(list_of_dicts)

    def _field_to_dict(self, values, name):
        """
        TODO: add docstring
        """
        def _build_dict_keys(system_bands_tuples, name):
            dict_keys = []
            for system_bands in system_bands_tuples:
                system = system_bands[0]
                bands = system_bands[1]
                for band in bands:
                    dict_keys.append(f'{system}_{name}_{band}')
            return dict_keys
        system_bands_tuples = [(phot_system.get_system_label(), phot_system.get_bands())
                                for phot_system in self.photometric_system]
        keys_list = _build_dict_keys(system_bands_tuples, name)
        values = _flatten_list(values)
        return {key: value for key, value in zip(keys_list, values)}
