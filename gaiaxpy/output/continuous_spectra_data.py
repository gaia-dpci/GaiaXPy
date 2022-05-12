"""
continuous_spectra_data.py
====================================
Module to represent continuous spectra data.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from astropy.io import fits
from astropy.io.votable.tree import Field, Resource, Table, VOTableFile
from fastavro import parse_schema, writer
from fastavro.validation import validate_many
from os.path import join
from .output_data import OutputData, _add_header, _build_regular_header
from gaiaxpy.core.satellite import BANDS


class ContinuousSpectraData(OutputData):

    def __init__(self, data):
        super().__init__(data, None)

    def _save_avro(self, output_path, output_file):
        """
        Save the output spectra in AVRO format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
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
                'bp_standard_deviation': 'float',
                'bp_coefficients': 'string',
                'bp_coefficient_correlations': 'string',
                'bp_coefficient_errors': 'string',
                'bp_n_parameters': 'int',
                'bp_basis_function_id': 'int',
                'rp_standard_deviation': 'float',
                'rp_coefficients': 'string',
                'rp_coefficient_correlations': 'string',
                'rp_coefficient_errors': 'string',
                'rp_n_parameters': 'int',
                'rp_basis_function_id': 'int'
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
                    if type == 'string':
                            spectrum[field] = str(tuple(spectrum[field]))
            # Validate that records match the schema
            validate_many(spectra_dicts, schema)
            return parse_schema(schema), spectra_dicts
        data = self.data
        # List with one dictionary per source
        spectra_dicts = data.to_dict('records')
        parsed_schema, spectra_dicts = _generate_avro_schema(spectra_dicts)
        Path(output_path).mkdir(parents=True, exist_ok=True)
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
        spectra_df = self.data
        array_columns = [column for column in spectra_df.columns if isinstance(spectra_df[column].iloc[0], np.ndarray)]
        spectra_df[array_columns] = spectra_df[array_columns].apply(lambda col: col.apply(tuple)).astype('str')
        Path(output_path).mkdir(parents=True, exist_ok=True)
        output_path = join(output_path, f'{output_file}.csv')
        spectra_df.to_csv(output_path, index=False)

    def _save_ecsv(self, output_path, output_file):
        """
        Save the output spectra in ECSV format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        spectra_df = self.data
        array_columns = [column for column in spectra_df.columns if isinstance(spectra_df[column].iloc[0], np.ndarray)]
        header_lines = _build_regular_header(array_columns)
        spectra_df[array_columns] = spectra_df[array_columns].apply(lambda col: col.apply(tuple)).astype('str')
        Path(output_path).mkdir(parents=True, exist_ok=True)
        output_path = join(output_path, f'{output_file}.ecsv')
        spectra_df.to_csv(output_path, index=False)
        _add_header(header_lines, output_file)

    def _save_fits(self, output_path, output_file):
        """
        Save the output data in FITS format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        data = self.data
        coefficients_format = f"{len(data['bp_coefficients'].iloc[0])}E"
        correlations_format = f"{len(data['bp_coefficient_correlations'].iloc[0])}E"
        # Define formats for each type according to FITS
        column_formats = {
            'source_id': 'K',
            'bp_standard_deviation': 'D',
            'bp_coefficients': coefficients_format,
            'bp_coefficient_correlations': correlations_format,
            'bp_coefficient_errors': coefficients_format,
            'bp_n_parameters': 'I',
            'bp_basis_function_id': 'I',
            'rp_standard_deviation': 'D',
            'rp_coefficients': coefficients_format,
            'rp_coefficient_correlations': correlations_format,
            'rp_coefficient_errors': coefficients_format,
            'rp_n_parameters': 'I',
            'rp_basis_function_id': 'I'}
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
        def _create_fields(votable, columns):
            # self.basis_function_id = {BANDS.bp: 56, BANDS.rp: 57}
            fields_datatypes = {'source_id': 'long',
                                f'{BANDS.bp}_standard_deviation': 'double',
                                f'{BANDS.bp}_coefficients': 'double',
                                f'{BANDS.bp}_coefficient_correlations': 'double',
                                f'{BANDS.bp}_coefficient_errors': 'double',
                                f'{BANDS.bp}_n_parameters': 'int',
                                f'{BANDS.bp}_basis_function_id': 'int',
                                f'{BANDS.rp}_standard_deviation': 'double',
                                f'{BANDS.rp}_coefficients': 'double',
                                f'{BANDS.rp}_coefficient_correlations': 'double',
                                f'{BANDS.rp}_coefficient_errors': 'double',
                                f'{BANDS.rp}_n_parameters': 'int',
                                f'{BANDS.rp}_basis_function_id': 'int'}
            fields_arraysize = {'source_id': '',
                                f'{BANDS.bp}_standard_deviation': '',
                                f'{BANDS.bp}_coefficients': '*',
                                f'{BANDS.bp}_coefficient_correlations': '*',
                                f'{BANDS.bp}_coefficient_errors': '*',
                                f'{BANDS.bp}_n_parameters': '',
                                f'{BANDS.bp}_basis_function_id': '',
                                f'{BANDS.rp}_standard_deviation': '',
                                f'{BANDS.rp}_coefficients': '*',
                                f'{BANDS.rp}_coefficient_correlations': '*',
                                f'{BANDS.rp}_coefficient_errors': '*',
                                f'{BANDS.rp}_n_parameters': '',
                                f'{BANDS.rp}_basis_function_id': ''}
            fields = [Field(votable, name=column, datatype=fields_datatypes[column], arraysize=fields_arraysize[column])
                      if fields_arraysize[column] != '' else Field(votable, name=column,
                      datatype=fields_datatypes[column]) for column in columns]
            return fields
        spectra_df = self.data
        # Create a new VOTable file
        votable = VOTableFile()
        # Add a resource
        resource = Resource()
        votable.resources.append(resource)
        # Add a table for the spectra (and add the sampling as metadata)
        spectra_table = Table(votable)
        resource.tables.append(spectra_table)
        # Add spectrum fields
        fields = _create_fields(votable, spectra_df.columns)
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

    def _get_spectra_df(self):
        data = self.data
        spectra_bp_df = pd.DataFrame.from_records(
                        [spectrum[BANDS.bp]._spectrum_to_dict() for spectrum in data])
        spectra_rp_df = pd.DataFrame.from_records(
                        [spectrum[BANDS.rp]._spectrum_to_dict() for spectrum in data])
        spectra_df = spectra_bp_df.merge(spectra_rp_df, on='source_id', how='outer')
        for col in spectra_df.columns:
            if 'xp' in col:
                spectra_df = spectra_df.drop(col, axis=1)
            else:
                if '_x' in col:
                    col_new = col.replace('_x', '')
                    col_new = f'{BANDS.bp}_' + col_new
                    spectra_df = spectra_df.rename(columns={col: col_new})
                if '_y' in col:
                    col_new = col.replace('_y', '')
                    col_new = f'{BANDS.rp}_' + col_new
                    spectra_df = spectra_df.rename(columns={col: col_new})
        return spectra_df
