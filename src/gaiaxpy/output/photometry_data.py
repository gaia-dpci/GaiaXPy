"""Save synthetic photometry tables and their GaiaXPy output metadata."""

from astropy.io import fits
from astropy.io.votable import from_table, writeto
from astropy.io.votable.tree import Param
from astropy.table import Table
from fastavro import parse_schema, writer
from fastavro.validation import validate_many

from gaiaxpy.core.output_metadata import OUTPUT_METADATA_KEY
from .metadata import (FITS_METADATA_KEY, encode_output_metadata, escape_xml_metadata,
                       save_csv_metadata)
from .output_data import OutputData
from .utils import _add_ecsv_header, _build_photometry_header, _prepare_output_path


class PhotometryData(OutputData):
    """Write already-computed synthetic photometry without a sampling grid.

    System and version labels are retained in column names. CSV stores GaiaXPy
    metadata in a companion file; the other writers embed it. Additional-system
    identity and configuration details are taken from the supplied metadata, not
    reconstructed from the column names.
    """

    def __init__(self, data):
        """Copy a photometry table and its DataFrame attrs for saving.

        Args:
            data (pandas.DataFrame): Photometry result containing source_id and
                system/passband columns, with optional gaiaxpy_metadata in attrs.
        """
        super().__init__(data, None)

    def _save_avro(self, output_path, output_file):
        """Write scalar photometry records to an Avro container.
        Avro support is intended for internal use only.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Notes:
            source_id uses a long integer. Columns containing _within_range_ use
            booleans; other fields use single-precision floats. The table must contain
            at least one row and values compatible with that schema. GaiaXPy metadata
            is stored in the container header when present.
        """

        def build_field(keys):
            """Assign long, boolean or float Avro types from the photometry column names."""
            return [{'name': key, 'type': 'long' if key == 'source_id' else
            'boolean' if '_within_range_' in key else 'float'} for key in keys]

        metadata_json = encode_output_metadata(self.data)
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
        full_output_path = _prepare_output_path(output_path, output_file, 'avro')
        with open(full_output_path, 'wb') as output:
            writer(output, parsed_schema, phot_list,
                   metadata={OUTPUT_METADATA_KEY: metadata_json} if metadata_json is not None else None)

    def _save_csv(self, output_path, output_file):
        """Write an ordinary photometry CSV and its optional metadata companion.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Notes:
            The main file has a column header and no DataFrame index or metadata
            comment line. GaiaXPy metadata is written to <output_file>_metadata.csv
            when present; an old companion is removed when metadata is absent.
        """
        photometry_df = self.data
        metadata_json = encode_output_metadata(photometry_df)
        full_output_path = _prepare_output_path(output_path, output_file, 'csv')
        with open(full_output_path, 'w', encoding='utf-8', newline='') as stream:
            photometry_df.to_csv(stream, index=False)
        save_csv_metadata(full_output_path, metadata_json)

    def _save_ecsv(self, output_path, output_file):
        """Write photometry with ECSV column declarations and optional metadata.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Notes:
            Columns must be source_id or follow the system/quantity/passband naming
            convention recognised by _build_photometry_header. Numeric type declarations
            come from the bundled header dictionary. GaiaXPy metadata is embedded in
            the ECSV table metadata when present.
        """
        photometry_df = self.data
        metadata_json = encode_output_metadata(photometry_df)
        header_lines = _build_photometry_header(photometry_df.columns)
        if metadata_json is not None:
            header_lines += f'# meta:\n#   {OUTPUT_METADATA_KEY}: {metadata_json}\n'
        full_output_path = _prepare_output_path(output_path, output_file, 'ecsv')
        photometry_df.to_csv(full_output_path, index=False)
        _add_ecsv_header(header_lines, full_output_path)

    def _save_fits(self, output_path, output_file):
        """Write a FITS photometry table and primary-header metadata.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Notes:
            Column types are inferred by Astropy from the DataFrame. GaiaXPy metadata
            is stored under GXPMETA in the primary header when present.
        """
        photometry_df = self.data
        metadata_json = encode_output_metadata(photometry_df)
        table = Table.from_pandas(photometry_df)
        hdu_list = list()
        hdr = fits.Header()
        if metadata_json is not None:
            hdr[FITS_METADATA_KEY] = metadata_json
        primary_hdu = fits.PrimaryHDU(header=hdr)
        hdu_list.append(primary_hdu)
        hdu = fits.table_to_hdu(table)
        hdu_list.append(hdu)
        # Put all HDUs together
        hdul = fits.HDUList(hdu_list)
        full_output_path = _prepare_output_path(output_path, output_file, 'fits')
        hdul.writeto(full_output_path, overwrite=True)

    def _save_xml(self, output_path, output_file):
        """Write photometry as an XML/VOTable with optional GaiaXPy metadata.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Notes:
            Astropy infers the table's column types. GaiaXPy metadata is stored in
            a gaiaxpy_metadata PARAM when present.
        """
        photometry_df = self.data
        metadata_json = encode_output_metadata(photometry_df)
        table = Table.from_pandas(photometry_df)
        votable = from_table(table)
        if metadata_json is not None:
            votable.get_first_table().params.append(Param(
                votable, name=OUTPUT_METADATA_KEY, datatype='char', arraysize='*',
                value=escape_xml_metadata(metadata_json)))
        full_output_path = _prepare_output_path(output_path, output_file, 'xml')
        writeto(votable, str(full_output_path))
