from itertools import islice
from pathlib import Path

import numpy as np
import numpy.testing as npt
import pandas as pd
import pytest

from gaiaxpy import convert
from gaiaxpy.converter.config import get_transposed_design_matrices
from gaiaxpy.converter.converter import _create_spectrum
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS, COV_INPUT_COLUMNS
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.xp_sampled_spectrum import XpSampledSpectrum
from tests.files.continuous import (dr3_mean_spectra_avro_file, dr3_mean_spectra_csv_file, dr3_mean_spectra_ecsv_file,
                                    dr3_mean_spectra_fits_file, dr3_mean_spectra_xml_binary_file,
                                    dr3_mean_spectra_xml_plain_file)
from tests.reference.converter import optimised_bases_df, converter_csv_solution_0_60_481_df
from tests.utils.utils import is_instance_err_message, assert_dfs_equal

con_input_files = [dr3_mean_spectra_avro_file, dr3_mean_spectra_csv_file, dr3_mean_spectra_ecsv_file,
                   dr3_mean_spectra_fits_file,
                   dr3_mean_spectra_xml_binary_file, dr3_mean_spectra_xml_plain_file]

TOL = 4
_rtol, _atol = 1e-7, 1e-7  # Precision varies with extension


@pytest.fixture(scope='module')
def sampling():
    yield np.linspace(0, 60, 481)


@pytest.mark.parametrize('file', con_input_files)
def test_get_design_matrices(file, sampling):
    instance = SampledBasisFunctions
    style_columns = COV_INPUT_COLUMNS if Path(file).suffix == '.avro' else CORR_INPUT_COLUMNS
    parser = InternalContinuousParser(MANDATORY_INPUT_COLS['convert'] + style_columns)
    parsed_input, _ = parser.parse_file(file)
    design_matrices = get_transposed_design_matrices(sampling, optimised_bases_df)
    assert len(design_matrices) == 2
    assert list(design_matrices.keys()) == list(BANDS)
    assert isinstance(design_matrices, dict), is_instance_err_message(file, dict)
    assert isinstance(design_matrices[BANDS.bp], instance), is_instance_err_message(file, instance)
    assert isinstance(design_matrices[BANDS.rp], instance), is_instance_err_message(file, instance)


@pytest.mark.parametrize('file', con_input_files)
def test_create_spectrum(file, sampling):
    spectrum = dict()
    truncation = True
    instance = XpSampledSpectrum
    parsed_input, _, _ = InputReader(file, convert, truncation=truncation, release=RELEASES.dr3).read()
    design_matrices = get_transposed_design_matrices(sampling, optimised_bases_df)
    for row in islice(parsed_input.itertuples(index=False), 1):  # Just the first row
        for band in BANDS:
            spectrum[band] = _create_spectrum(row, truncation, design_matrices, band)
    assert spectrum[BANDS.bp].get_source_id() == spectrum[BANDS.rp].get_source_id()
    for band in BANDS:
        assert isinstance(spectrum[band], instance), is_instance_err_message(file, instance, band)
        assert spectrum[band].get_band() == band


@pytest.mark.parametrize('file', con_input_files)
def test_converter_both_types(file, sampling):
    converted_df, _ = convert(file, sampling=sampling, save_file=False, release=RELEASES.dr3)
    assert isinstance(converted_df, pd.DataFrame)
    assert len(converted_df) == 4
    assert_dfs_equal(converted_df, converter_csv_solution_0_60_481_df, rtol=_rtol, atol=_atol)


@pytest.mark.parametrize('file', con_input_files)
@pytest.mark.parametrize('_sampling', [np.linspace(-15, 60, 600), np.linspace(-10, 71, 600),
                                       np.linspace(-11, 71, 600), None])
def test_sampling_error(file, _sampling):
    with pytest.raises(ValueError):
        convert(file, sampling=_sampling, save_file=False, release=RELEASES.dr3)


@pytest.mark.parametrize('file', con_input_files)
def test_sampling_equal(file, sampling):
    _, _positions = convert(file, sampling=sampling, truncation=True, save_file=False, release=RELEASES.dr3)
    npt.assert_array_equal(sampling, _positions)


def test_convert_accepts_single_spectrum_series(sampling):
    spectra, _, _ = InputReader(dr3_mean_spectra_csv_file, convert, truncation=False, release=RELEASES.dr3).read()
    kwargs = dict(sampling=sampling, save_file=False, release=RELEASES.dr3)
    expected, expected_sampling = convert(spectra.iloc[[0]], **kwargs)
    actual, actual_sampling = convert(spectra.iloc[0], **kwargs)

    assert actual['source_id'].unique().tolist() == spectra['source_id'].iloc[:1].tolist()
    assert_dfs_equal(actual, expected)
    npt.assert_array_equal(actual_sampling, expected_sampling)
