"""
line_data.py
====================================
Module to represent a photometry dataframe.
"""
from os.path import join
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.io.votable import from_table, writeto
from astropy.table import Table

from .output_data import OutputData, _add_header, _build_line_header


class LineData(OutputData):

    def __init__(self, data):
        super().__init__(data, None)

    def _save_avro(self, output_path, output_file):
        """
        Save the output photometry in AVRO format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        raise NotImplementedError('AVRO output is not implemented for linefinder functions.')

    def _save_csv(self, output_path, output_file):
        """
        Save the output photometry in CSV format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        line_df = self.data
        array_columns = [column for column in line_df.columns if isinstance(line_df[column].iloc[0], np.ndarray)]
        line_df[array_columns] = line_df[array_columns].apply(lambda col: col.apply(tuple)).astype('str')
        Path(output_path).mkdir(parents=True, exist_ok=True)
        output_path = join(output_path, f'{output_file}.csv')
        line_df.to_csv(output_path, index=False)

    def _save_ecsv(self, output_path, output_file):
        """
        Save the output photometry in ECSV format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        line_df = self.data
        header_lines = _build_line_header(line_df.columns)
        Path(output_path).mkdir(parents=True, exist_ok=True)
        line_df.to_csv(join(output_path, f'{output_file}.ecsv'), index=False)
        _add_header(header_lines, output_path, output_file)

    def _save_fits(self, output_path, output_file):
        """
        Save the output photometry in FITS format.

        Args:
            output_path (str): Path where to save the file.
            output_file (str): Name chosen for the output file.
        """
        line_df = self.data
        table = Table.from_pandas(line_df)
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
        line_df = self.data
        table = Table.from_pandas(line_df)
        votable = from_table(table)
        Path(output_path).mkdir(parents=True, exist_ok=True)
        output_path = join(output_path, f'{output_file}.xml')
        writeto(votable, output_path)
