"""Save sampled spectra from calibrate and convert, along with their sampling.

CSV and Avro use separate sampling files; ECSV, FITS and XML/VOTable
store the sampling within the main output. GaiaXPy metadata is saved separately
for CSV and embedded for the other formats. The Gaia Archive does not distribute
Avro files. Avro support is intended for internal use only.
"""

import warnings
from os.path import join
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.io.votable.tree import Field, Param, Resource, VOTableFile
from astropy.units import UnitsWarning
from fastavro import parse_schema, writer
from fastavro.validation import validate_many

from gaiaxpy.core.output_metadata import OUTPUT_METADATA_KEY
from .metadata import (FITS_METADATA_KEY, encode_output_metadata, escape_xml_metadata,
                       save_csv_metadata)
from .output_data import OutputData
from .utils import (_add_ecsv_header, _array_to_standard, _build_ecsv_header, _generate_fits_header,
                    _get_sampling_dict, _load_header_dict, _get_col_subtype_len, _prepare_output_path)

try:
    from astropy.io.votable.tree import TableElement as ATable
except ImportError:
    from astropy.io.votable.tree import Table as ATable


class SampledSpectraData(OutputData):
    """Write already-computed flux and flux-error arrays on a common grid.

    Optional columns include xp, packed correlations and standard_deviation.
    The data_type attr supplies units for ECSV, FITS and XML/VOTable. Saved numeric
    types depend on the format; identical precision across formats cannot be guaranteed.
    """

    _sampling_companion_formats = ('csv', 'avro')

    def __init__(self, data, positions):
        """Copy the spectrum table and retain the common sampling grid.

        Args:
            data (pandas.DataFrame): Sampled spectra returned by calibration or
                conversion. Rows contain source_id, flux and flux_error, with any
                additional supported spectrum columns and output attrs.
            positions (array-like): Sampling shared by the flux and error arrays.
        """
        super().__init__(data, positions)

    def _save_avro(self, output_path, output_file):
        """Write spectra and a separate sampling file in Avro format.
        Avro support is intended for internal use only.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Notes:
            Write <output_file>.avro and <output_file>_sampling.avro. Array fields
            are stored as tuple text; the sampling record has a string-valued pos field.
            GaiaXPy metadata is embedded in the main container header when present.
            The table must be non-empty and its array cells must be iterable. The
            standard_deviation field uses single precision.
        """

        def _save_avro_sampling(_positions, _output_path, _output_file):
            """Write the common sampling as a string-valued pos record in an Avro companion.

            Args:
                _positions (array-like): Common sampling grid.
                _output_path (str or pathlib.Path): Existing destination directory.
                _output_file (str): Main filename stem, before the _sampling suffix.
            """
            schema = {'doc': 'Output sampling.', 'name': 'Sampling', 'namespace': 'sampling', 'type': 'record',
                      'fields': [{'name': 'pos', 'type': 'string'}, ], }
            # Must be an iterable
            sampling = [_get_sampling_dict(_positions)]
            # Sampling field to string
            sampling[0]['pos'] = str(sampling[0]['pos'])
            # Validate that records match the schema
            validate_many(sampling, schema)
            _parsed_schema = parse_schema(schema)
            with open(join(_output_path, f'{_output_file}_sampling.avro'), 'wb') as _output:
                writer(_output, _parsed_schema, sampling)

        def _generate_avro_schema(_spectra_dicts):
            """Build the sampled-spectrum schema and serialise array fields in the records.

            Args:
                _spectra_dicts (list[dict]): Non-empty record list with supported spectrum
                    columns. Array fields must be iterable.

            Returns:
                tuple[dict, list[dict]]: Parsed Avro schema and the supplied records,
                modified in place to contain tuple text for array fields. Records are
                validated before return.
            """
            field_to_type = {'source_id': 'long', 'xp': 'string', 'flux': 'string', 'flux_error': 'string',
                             'correlation': 'string', 'standard_deviation': 'float'}

            def build_field(keys):
                """Map supported sampled-spectrum column names to their Avro field definitions."""
                return [{'name': key, 'type': field_to_type[key]} for key in keys]

            schema = {'doc': 'Spectrum output.', 'name': 'Spectra', 'namespace': 'spectrum', 'type': 'record',
                      'fields': build_field(_spectra_dicts[0].keys()), }
            # Spectrum fields to string
            for spectrum in _spectra_dicts:
                for field, _type in field_to_type.items():
                    if _type == 'string' and field in spectrum.keys() and not field == 'xp':
                        spectrum[field] = str(tuple(spectrum[field]))
            # Validate that records match the schema
            validate_many(_spectra_dicts, schema)
            return parse_schema(schema), _spectra_dicts

        metadata_json = encode_output_metadata(self.data)
        data = self.data
        positions = self.positions
        Path(output_path).mkdir(parents=True, exist_ok=True)
        _save_avro_sampling(positions, output_path, output_file)
        # List with one dictionary per source
        spectra_dicts = data.to_dict('records')
        parsed_schema, spectra_dicts = _generate_avro_schema(spectra_dicts)
        full_output_path = _prepare_output_path(output_path, output_file, 'avro')
        with open(full_output_path, 'wb') as output:
            writer(output, parsed_schema, spectra_dicts,
                   metadata={OUTPUT_METADATA_KEY: metadata_json} if metadata_json is not None else None)

    def _save_csv(self, output_path, output_file):
        """Write sampled spectra, sampling and optional metadata as CSV files.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Notes:
            Write <output_file>.csv and <output_file>_sampling.csv. Array cells use
            tuple text; the sampling file has one pos cell containing the common grid.
            When GaiaXPy metadata is present, write <output_file>_metadata.csv as well.
            If it is absent, remove any old metadata companion. The main CSV contains
            an ordinary column header without a metadata comment line.
        """
        data = self.data
        positions = self.positions
        modified_data = data.map(lambda x: _array_to_standard(x) if isinstance(x, np.ndarray) else x)
        metadata_json = encode_output_metadata(data)
        full_output_path = _prepare_output_path(output_path, output_file, 'csv')
        with open(full_output_path, 'w', encoding='utf-8', newline='') as stream:
            modified_data.to_csv(stream, index=False)
        save_csv_metadata(full_output_path, metadata_json)
        # Assume the sampling is the same for all spectra
        pos = [str(_array_to_standard(positions))]
        sampling_df = pd.DataFrame({'pos': pos})
        sampling_df.to_csv(join(output_path, f'{output_file}_sampling.csv'), index=False)

    def _save_ecsv(self, output_path, output_file):
        """Write sampled spectra with an ECSV header and embedded sampling.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Notes:
            Array cells use square-bracket representations and null for NaN values.
            The header declares column types and units and includes the sampling grid.
            GaiaXPy metadata is included in table metadata when present. Declared
            numeric types come from the bundled header dictionary.
        """
        data = self.data
        positions = self.positions
        modified_data = data.map(lambda x: _array_to_standard(x, 'ecsv') if isinstance(x, np.ndarray) else x)
        header_lines = _build_ecsv_header(modified_data, positions)
        metadata_json = encode_output_metadata(data)
        if metadata_json is not None:
            if '# meta:\n' not in header_lines:
                header_lines += '# meta:\n'
            header_lines += f'#   {OUTPUT_METADATA_KEY}: {metadata_json}\n'
        full_output_path = _prepare_output_path(output_path, output_file, 'ecsv')
        modified_data.to_csv(full_output_path, index=False)
        _add_ecsv_header(header_lines, full_output_path)

    def _save_fits(self, output_path, output_file):
        """Write a primary FITS header and a binary spectrum table.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Notes:
            The primary header stores GaiaXPy metadata under GXPMETA when present.
            Sampling is stored in the binary-table header under Sampling. Flux and
            correlation fields use double precision; flux errors and standard_deviation
            use single precision. Rows with None flux cells select variable-length
            array columns.
        """
        warnings.filterwarnings('ignore', category=UnitsWarning)

        def _flux_contains_none(arrays):
            """Return whether any flux cell is None, requiring variable-length FITS arrays."""
            return any(arr is None for arr in arrays['flux'])

        data = self.data
        metadata_json = encode_output_metadata(data)
        positions = self.positions
        # Create a list of HDUs
        hdu_list = list()
        # create a header to include the sampling
        hdr = fits.Header()
        if metadata_json is not None:
            hdr[FITS_METADATA_KEY] = metadata_json
        primary_hdu = fits.PrimaryHDU(header=hdr)
        hdu_list.append(primary_hdu)
        # Create a dictionary to hold all the data
        output_by_column_dict = data.reset_index().to_dict(orient='list')
        # Remove index from output dict
        output_by_column_dict.pop('index', None)
        spectra_keys = output_by_column_dict.keys()
        data_type = data.attrs['data_type']
        units_dict = data_type.get_units()
        pos_len = len(positions)
        contains_none = _flux_contains_none(output_by_column_dict)
        # D: double precision float
        flux_format = 'PD()' if contains_none else f'{pos_len}D'
        # E: single precision float
        flux_error_format = 'PE()' if contains_none else f'{pos_len}E'
        aux_corr = data.get('correlation')
        correlation_format = ''
        if aux_corr is not None:
            correlation_format = 'PD()' if contains_none else f"{_get_col_subtype_len(data, 'correlation')}D"
        # Define formats for each type according to FITS
        column_formats = {'source_id': 'K', 'xp': '2A', 'flux': flux_format, 'flux_error': flux_error_format,
                          'correlation': correlation_format, 'standard_deviation': 'E'}
        columns = [
            fits.Column(name=key, array=[value if value is not None else [] for value in output_by_column_dict[key]],
                        format=column_formats[key], unit=units_dict.get(key, '')) for key in spectra_keys]
        header = _generate_fits_header(data, column_formats)
        header['Sampling'] = str(tuple(positions))
        hdu = fits.BinTableHDU.from_columns(columns, header=header)
        hdu_list.append(hdu)
        # Put all HDUs together
        hdul = fits.HDUList(hdu_list)
        # Write the file and replace it if it already exists
        full_output_path = _prepare_output_path(output_path, output_file, 'fits')
        hdul.writeto(full_output_path, overwrite=True)

    def _save_xml(self, output_path, output_file):
        """Write sampled spectra and their sampling as an XML/VOTable.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Notes:
            The sampling grid is stored in a sampling PARAM, and GaiaXPy metadata
            in a gaiaxpy_metadata PARAM when present. Flux and correlations use double
            precision; flux errors and standard_deviation use single precision.
            Units and column descriptions come from data_type and the bundled headers.
        """
        warnings.filterwarnings('ignore', category=UnitsWarning)

        def _create_params(_votable, sampling, data_type):
            """Build the double-precision sampling PARAM with units from data_type."""
            column = 'sampling'
            unit = data_type.get_units().get('pos', '')
            return [Param(_votable, name=column, ID=f'_{column}', ucd='em.wl', datatype='double', arraysize='*',
                          unit=unit, value=list(sampling))]

        def _create_fields(_votable, _spectra_df):
            """Build spectrum FIELD definitions, descriptions and array sizes for a VOTable."""
            _spectra_flux_len = _get_col_subtype_len(_spectra_df, 'flux')
            _spectra_flux_error_len = _get_col_subtype_len(_spectra_df, 'flux_error')
            len_flux = str(_spectra_flux_len)
            len_error = str(_spectra_flux_error_len)
            len_correlation = str(
                len(_spectra_df['correlation'].iloc[0])) if 'correlation' in _spectra_df.columns else ''
            fields_datatypes = {'source_id': 'long', 'xp': 'char', 'flux': 'double', 'flux_error': 'float',
                                'correlation': 'double', 'standard_deviation': 'float'}
            fields_array_size = {'source_id': '', 'xp': '2', 'flux': len_flux, 'flux_error': len_error,
                                 'correlation': len_correlation, 'standard_deviation': ''}
            fields_id = {key: f'_{key}' for key in ['source_id', 'xp', 'flux', 'flux_error', 'correlation']}
            fields_id.update({'source_id': None})
            header_dict = _load_header_dict()
            data_type = _spectra_df.attrs['data_type']
            units_dict = data_type.get_units()
            _fields = [Field(_votable, name=column, ucd=header_dict.get(column, dict()).get('meta', ''),
                             ID=fields_id[column], datatype=fields_datatypes[column],
                             arraysize=fields_array_size[column], unit=units_dict.get(column, None)) if
                       fields_array_size[column] != '' else Field(_votable, name=column,
                                                                  datatype=fields_datatypes[column],
                                                                  ucd=header_dict.get(column, dict()).get('meta', ''),
                                                                  unit=units_dict.get(column, None))
                       for column in _spectra_df.columns]
            for _field in _fields:
                _field.description = header_dict.get(_field.name, dict()).get('description', '')
            return _fields

        spectra_df = self.data
        metadata_json = encode_output_metadata(spectra_df)
        positions = list(self.positions)
        # Create a new VOTable file
        votable = VOTableFile()
        # Add a resource
        resource = Resource()
        votable.resources.append(resource)
        # Add a table for the spectra (and add the sampling as metadata)
        spectra_table = ATable(votable)
        resource.tables.append(spectra_table)
        # Add sampling as param
        params = _create_params(votable, positions, spectra_df.attrs['data_type'])
        spectra_table.params.extend(params)
        if metadata_json is not None:
            # Keep XML-sensitive characters as JSON escapes: PARAM serialisation
            # otherwise escapes these twice in some Astropy versions.
            metadata_json = escape_xml_metadata(metadata_json)
            spectra_table.params.append(Param(votable, name=OUTPUT_METADATA_KEY, datatype='char',
                                              arraysize='*', value=metadata_json))
        # Add spectrum fields
        fields = _create_fields(votable, spectra_df)
        spectra_table.fields.extend(fields)
        # Create the record arrays, with the given number of rows
        spectra_table.create_arrays(len(spectra_df))
        for index, row in enumerate(spectra_df.to_dict('records')):
            spectra_table.array[index] = tuple([row[column] for column in spectra_df.columns])
        # Write to a file
        full_output_path = _prepare_output_path(output_path, output_file, 'xml')
        votable.to_xml(str(full_output_path))
