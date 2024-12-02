from itertools import product

import pandas as pd
from gaiaxpy.generator.generator import generate
from gaiaxpy.generator.photometric_system import PhotometricSystem

from tests.files.paths import (mean_spectrum_csv_file, mean_spectrum_avro_file, mean_spectrum_fits_file,
                               mean_spectrum_xml_file)


def columns_from_vars(bands, label):
    cols_vars = ['mag', 'flux', 'flux_error']
    return ['source_id'] + [f'{label}_{var}_{band}' for var, band in product(cols_vars, bands)]


def test_generate_single():
    phot_system_johnson = PhotometricSystem.JKC
    phot_system_sdss = PhotometricSystem.SDSS
    jkc_columns = columns_from_vars(['U', 'B', 'V', 'R', 'I'], 'Jkc')
    sdss_columns = columns_from_vars(['u', 'g', 'r', 'i', 'z'], 'Sdss')
    input_files = [mean_spectrum_csv_file, mean_spectrum_fits_file, mean_spectrum_avro_file, mean_spectrum_xml_file]
    phot_systems = [phot_system_johnson, phot_system_johnson, phot_system_sdss, phot_system_sdss]
    output_columns = [jkc_columns, jkc_columns, sdss_columns, sdss_columns]
    for file, syst, cols in zip(input_files, phot_systems, output_columns):
        synthetic_photometry = generate(file, photometric_system=syst, save_file=False)
        assert isinstance(synthetic_photometry, pd.DataFrame)
        assert len(synthetic_photometry) == 2
        assert list(synthetic_photometry.columns) == cols
