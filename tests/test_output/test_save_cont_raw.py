from os.path import join

import numpy as np
import pandas as pd
import pytest
from astropy.io.votable import parse_single_table
from astropy.table import Table

from gaiaxpy import calibrate, convert, generate, PhotometricSystem
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.file_parser.parse_generic import GenericParser
from tests.files.continuous import dr3_mean_spectra_csv_file
from tests.files.misc import output_sol_path
from tests.utils.utils import assert_dfs_equal

_rtol, _atol = 1e-10, 1e-10


def compare_frames(output_file, solution_file, extension, function_name):
    def _parse_output_fits(fits_file, _array_columns=None):
        table = Table.read(fits_file, format='fits')
        columns = table.columns.keys()
        fits_as_gen = ([table[column][index] for column in columns] for index, _ in enumerate(table))
        return pd.DataFrame(fits_as_gen, columns=columns)

    def _parse_output_xml(xml_file, _array_columns=None):
        votable = parse_single_table(xml_file).to_table(use_names_over_ids=True)
        if _array_columns:
            columns = list(votable.columns)
            votable_as_list = ([votable[column][index].filled() if column in _array_columns else votable[column][index]
                                for column in columns] for index, _ in enumerate(votable))
            df = pd.DataFrame(votable_as_list, columns=columns)
        else:
            df = votable.to_pandas()
        return df

    parser = GenericParser()
    function, array_columns = None, None
    if function_name in ['calibrate', 'convert']:
        array_columns = ['flux', 'flux_error']
    if extension in ['csv', 'ecsv']:
        function = parser._parse_csv
    elif extension == 'fits':
        function = _parse_output_fits
    elif extension == 'xml':
        function = _parse_output_xml
    if array_columns:
        output_df = function(output_file, _array_columns=array_columns)
        solution_df = function(solution_file, _array_columns=array_columns)
    else:
        output_df = function(output_file)
        solution_df = function(solution_file)

    assert_dfs_equal(output_df, solution_df, rtol=_rtol, atol=_atol)


def run_output_test(output_path, function, filename, output_format, sampling=None, phot_systems=None):
    """
    This class generates GaiaXPy output files. Then, it compares them with the output solution files using filecmp.
    """
    input_file = dr3_mean_spectra_csv_file
    release = RELEASES.dr3
    if sampling is not None:
        function(input_file, sampling=sampling, output_path=output_path, output_file=filename,
                 output_format=output_format, release=release)
    if phot_systems is not None:
        _ = function(input_file, photometric_system=phot_systems, output_path=output_path, output_file=filename,
                     output_format=output_format, release=release)
    elif sampling is None and phot_systems is None:
        function(input_file, output_path=output_path, output_file=filename, output_format=output_format,
                 release=release)
    current_file = f'{filename}.{output_format}'
    print(join(output_path, current_file), join(output_sol_path, current_file), output_format)
    compare_frames(join(output_path, current_file), join(output_sol_path, current_file), extension=output_format,
                   function_name=function.__name__)
    if output_format in ['csv', '.csv'] and phot_systems is None and 'find' not in function.__name__:
        # A sampling file will be generated too (calibrate and convert), it needs to be tested
        current_sampling_file = f'{filename}_sampling.{output_format}'
        compare_frames(join(output_path, current_sampling_file), join(output_sol_path, current_sampling_file),
                       extension=output_format, function_name=function.__name__)


@pytest.mark.parametrize('extension', ['csv', 'ecsv', 'fits', 'xml'])
def test_save_output_calibrator(extension, tmp_path):
    run_output_test(tmp_path, calibrate, 'calibrator', extension)


@pytest.mark.parametrize('extension', ['csv', 'ecsv', 'fits', 'xml'])
def test_save_output_converter(extension, tmp_path):
    run_output_test(tmp_path, convert, 'converter', extension)


@pytest.mark.parametrize('name,extension,sampling', [['converter_custom_0_40_350', 'csv', np.linspace(0, 40, 350)],
                                                     ['converter_custom_0_45_400', 'fits', None],
                                                     ['converter_custom_0_30_300', 'xml', None]])
def test_save_output_convert(tmp_path, name, extension, sampling):
    if sampling is not None:
        run_output_test(tmp_path, convert, name, extension, sampling=sampling)
    else:
        run_output_test(tmp_path, convert, name, extension)


@pytest.mark.parametrize('name,extension,systems', [['photometry_gaia_2', 'csv', PhotometricSystem.DR3_Gaia_2],
                                                    ['photometry_sdss_std', 'ecsv', PhotometricSystem.DR3_SDSS_Std],
                                                    ['photometry_multi', 'fits', [PhotometricSystem.DR3_Gaia_Vega,
                                                                                  PhotometricSystem.DR3_HST_HUGS_Std]],
                                                    ['photometry_pristine', 'xml', [PhotometricSystem.DR3_Pristine]]])
def test_save_output_generate(tmp_path, name, extension, systems):
    run_output_test(tmp_path, generate, name, extension, phot_systems=systems)
