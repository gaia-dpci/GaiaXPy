"""
sampled_spectra_dataframe.py
====================================
Module to represent a dataframe of sampled spectra.
"""

import numpy as np
import pandas as pd
from fastavro import parse_schema, writer
from pathlib import Path
from astropy.io import fits
from astropy.io.votable.tree import Field, Param, Resource, Table, VOTableFile
from fastavro.validation import validate_many
from os.path import join
from numpy import ndarray
from .output_data import OutputData, _add_header, _build_regular_header
from .utils import _array_to_standard, _get_sampling_dict


class SampledSpectraData(OutputData):

    def __init__(self, data, positions):
        super().__init__(data, positions)

    def _save_avro(self, output_path, output_file):
        """
        Save the output spectra in AVRO format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        def _save_sampling_avro(positions, output_path, output_file):
            """
            Save the sampling in a separate avro file.

            Args:
                spectra (list): List of output spectra
                output_file (str): Name of the output file.
            """
            schema = {
                'doc': 'Output sampling.',
                'name': 'Sampling',
                'namespace': 'sampling',
                'type': 'record',
                'fields': [
                    {'name': 'pos', 'type': 'string'},
                ],
            }
            # Must be an iterable
            sampling = [_get_sampling_dict(positions)]
            # Sampling field to string
            sampling[0]['pos'] = str(sampling[0]['pos'])
            # Validate that records match the schema
            validate_many(sampling, schema)
            parsed_schema = parse_schema(schema)
            output_path = join(output_path, f'{output_file}_sampling.avro')
            with open(output_path, 'wb') as output:
                writer(output, parsed_schema, sampling)

        def _generate_avro_schema(spectra_dicts):
            """
            Generate the AVRO schema required to store the output.

            Args:
                spectra_dicts (list): A list of dictionaries containing spectra.

            Returns:
                dict: A dictionary containing the parsed schema that matches the input.
                list of dicts: A list of dictionaries with the modified input spectra
                according to the valid AVRO types.
            """
            field_to_type = {
                'source_id': 'long',
                'xp': 'string',
                'flux': 'string',
                'flux_error': 'string'
            }

            def build_field(keys):
                fields = []
                for key in keys:
                    field = {'name': key, 'type': field_to_type[key]}
                    fields.append(field)
                return fields
            schema = {
                'doc': 'Spectrum output.',
                'name': 'Spectra',
                'namespace': 'spectrum',
                'type': 'record',
                'fields': build_field(spectra_dicts[0].keys()),
            }
            # Spectrum fields to string
            for spectrum in spectra_dicts:
                for field, type in field_to_type.items():
                    if type == 'string' and not field == 'xp':
                        try:
                            spectrum[field] = str(tuple(spectrum[field]))
                        except KeyError:
                            # Key may not exist (e.g.: 'xp')
                            continue
            # Validate that records match the schema
            validate_many(spectra_dicts, schema)
            return parse_schema(schema), spectra_dicts
        data = self.data
        positions = self.positions
        Path(output_path).mkdir(parents=True, exist_ok=True)
        _save_sampling_avro(positions, output_path, output_file)
        # List with one dictionary per source
        spectra_dicts = data.to_dict('records')
        parsed_schema, spectra_dicts = _generate_avro_schema(spectra_dicts)
        output_path = join(output_path, f'{output_file}.avro')
        with open(output_path, 'wb') as output:
            writer(output, parsed_schema, spectra_dicts)

    def _save_csv(self, output_path, output_file):
        """
        Save the output spectra in CSV format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        data = self.data
        positions = self.positions
        modified_data = data.applymap(lambda x: _array_to_standard(x) if isinstance(x, ndarray) else x)
        Path(output_path).mkdir(parents=True, exist_ok=True)
        modified_data.to_csv(join(output_path, f'{output_file}.csv'), index=False)
        # Assuming the sampling is the same for all spectra
        pos = [str(_array_to_standard(positions))]
        sampling_df = pd.DataFrame({'pos': pos})
        sampling_df.to_csv(join(output_path, f'{output_file}_sampling.csv'), index=False)

    def _save_ecsv(self, output_path, output_file):
        """
        Save the output spectra in ECSV format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        data = self.data
        positions = self.positions
        modified_data = data.applymap(lambda x: _array_to_standard(x) if isinstance(x, ndarray) else x)
        header_lines = _build_regular_header(modified_data.columns)
        Path(output_path).mkdir(parents=True, exist_ok=True)
        modified_data.to_csv(join(output_path, f'{output_file}.ecsv'), index=False)
        _add_header(header_lines, output_path, output_file)
        # Assuming the sampling is the same for all spectra
        pos = [str(_array_to_standard(positions))]
        sampling_df = pd.DataFrame({'pos': pos})
        header_lines = _build_regular_header(sampling_df.columns)
        sampling_df.to_csv(join(output_path, f'{output_file}_sampling.ecsv'), index=False)
        _add_header(header_lines, output_path, f'{output_file}_sampling')

    def _save_fits(self, output_path, output_file):
        """
        Save the output data in FITS format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        data = self.data
        positions = self.positions
        # Get length of flux (should be the same as length of error)
        flux_format = f"{len(positions)}E"  # E: single precision floating
        # Define formats for each type according to FITS
        column_formats = {
            'source_id': 'K',
            'xp': '2A',
            'flux': flux_format,
            'flux_error': flux_format}
        # create a list of HDUs
        hdu_list = []
        # create a header to include the sampling
        hdr = fits.Header()
        primary_hdu = fits.PrimaryHDU(header=hdr)
        hdu_list.append(primary_hdu)
        # Create a dictionary to hold all the data
        output_by_column_dict = data.reset_index().to_dict(orient='list')
        # Remove index from output dict
        output_by_column_dict.pop('index', None)
        spectra_keys = output_by_column_dict.keys()
        columns = []
        for key in spectra_keys:
            columns.append(fits.Column(name=key, array=np.array(output_by_column_dict[key]), format=column_formats[key]))
        header = fits.Header()
        header['Sampling'] = str(tuple(positions))
        hdu = fits.BinTableHDU.from_columns(columns, header=header)
        hdu_list.append(hdu)
        # Put all HDUs together
        hdul = fits.HDUList(hdu_list)
        # Write the file and replace it if it already exists
        Path(output_path).mkdir(parents=True, exist_ok=True)
        output_path = join(output_path, f'{output_file}.fits')
        hdul.writeto(output_path, overwrite=True)

    def _save_xml(self, output_path, output_file):
        """
        Save the output spectra in XML/VOTABLE format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        def _create_params(votable, sampling):
            column = 'sampling'
            params = [Param(votable, name=column, ID=f'_{column}', ucd='em.wl',
                      datatype='double', arraysize='*', value=list(sampling))]
            return params

        def _create_fields(votable, spectra_df):
            len_flux = str(len(spectra_df['flux'].iloc[0]))
            len_error = str(len(spectra_df['flux_error'].iloc[0]))
            fields_datatypes = {'source_id': 'long', 'xp': 'char', 'flux': 'double', 'flux_error': 'double'}
            fields_arraysize = {'source_id': '', 'xp': '2', 'flux': len_flux, 'flux_error': len_error}
            fields_ID = {'source_id': None, 'xp': '_xp', 'flux': '_flux', 'flux_error': '_flux_error'}
            fields_ucd = {'source_id': 'meta.id;meta.main', 'xp': 'temp', 'flux': 'phot.flux',
                          'flux_error': 'stat.error;phot.flux'}
            fields = [Field(votable, name=column, ucd=fields_ucd[column], ID=fields_ID[column],
                            datatype=fields_datatypes[column], arraysize=fields_arraysize[column])
                            if fields_arraysize[column] != '' else Field(votable, name=column,
                            datatype=fields_datatypes[column]) for column in spectra_df.columns]
            return fields
        spectra_df = self.data
        positions = list(self.positions)
        # Create a new VOTable file
        votable = VOTableFile()
        # Add a resource
        resource = Resource()
        votable.resources.append(resource)
        # Add a table for the spectra (and add the sampling as metadata)
        spectra_table = Table(votable)
        resource.tables.append(spectra_table)
        # Add sampling as param
        params = _create_params(votable, positions)
        spectra_table.params.extend(params)
        # Add spectrum fields
        fields = _create_fields(votable, spectra_df)
        spectra_table.fields.extend(fields)
        # Create the record arrays, with the given number of rows
        spectra_table.create_arrays(len(spectra_df))
        for index, row in spectra_df.iterrows():
            args = tuple([row[column] for column in spectra_df.columns])
            spectra_table.array[index] = args
        # Write to a file
        Path(output_path).mkdir(parents=True, exist_ok=True)
        output_path = join(output_path, f'{output_file}.xml')
        votable.to_xml(output_path)
