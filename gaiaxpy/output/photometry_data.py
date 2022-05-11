"""
photometry_dataframe.py
====================================
Module to represent a photometry dataframe.
"""
from pathlib import Path
from fastavro import parse_schema, writer
from astropy.io import fits
from astropy.io.votable import from_table, writeto
from astropy.table import Table
from fastavro.validation import validate_many
from os.path import join
from .output_data import OutputData, _add_header, _build_photometry_header


class PhotometryData(OutputData):

    def __init__(self, data):
        super().__init__(data, None)

    def _save_avro(self, output_path, output_file):
        """
        Save the output photometry in AVRO format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        def build_field(keys):
            fields = []
            for key in keys:
                if key == 'source_id':
                    field = {'name': key, 'type': 'long'}
                else:
                    field = {'name': key, 'type': 'float'}
                fields.append(field)
            return fields
        phot_list = self.data.to_dict('records')
        schema = {
            'doc': 'Output photometry.',
            'name': 'Photometry',
            'namespace': 'photometry',
            'type': 'record',
            'fields': build_field(phot_list[0].keys()),
        }
        validate_many(phot_list, schema)
        parsed_schema = parse_schema(schema)
        Path(output_path).mkdir(parents=True, exist_ok=True)
        output_path = join(output_path, f'{output_file}.avro')
        with open(output_path, 'wb') as output:
            writer(output, parsed_schema, phot_list)

    def _save_csv(self, output_path, output_file):
        """
        Save the output photometry in CSV format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        photometry_df = self.data
        Path(output_path).mkdir(parents=True, exist_ok=True)
        output_path = join(output_path, f'{output_file}.csv')
        photometry_df.to_csv(output_path, index=False)

    def _save_ecsv(self, output_path, output_file):
        """
        Save the output photometry in ECSV format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        photometry_df = self.data
        header_lines = _build_photometry_header(photometry_df.columns)
        Path(output_path).mkdir(parents=True, exist_ok=True)
        photometry_df.to_csv(join(output_path, f'{output_file}.ecsv'), index=False)
        _add_header(header_lines, output_path, output_file)

    def _save_fits(self, output_path, output_file):
        """
        Save the output photometry in FITS format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        photometry_df = self.data
        table = Table.from_pandas(photometry_df)
        hdu_list = []
        hdr = fits.Header()
        primary_hdu = fits.PrimaryHDU(header=hdr)
        hdu_list.append(primary_hdu)
        hdu = fits.table_to_hdu(table)
        hdu_list.append(hdu)
        # Put all HDUs together
        hdul = fits.HDUList(hdu_list)
        Path(output_path).mkdir(parents=True, exist_ok=True)
        output_path = join(output_path, f'{output_file}.fits')
        hdul.writeto(output_path, overwrite=True)

    def _save_xml(self, output_path, output_file):
        """
        Save the output photometry in XML/VOTABLE format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        photometry_df = self.data
        table = Table.from_pandas(photometry_df)
        votable = from_table(table)
        Path(output_path).mkdir(parents=True, exist_ok=True)
        output_path = join(output_path, f'{output_file}.xml')
        writeto(votable, output_path)
