from itertools import islice

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import convert
from gaiaxpy.converter.converter import _create_spectrum, get_design_matrices
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.file_parser.parse_internal_sampled import InternalSampledParser
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.xp_sampled_spectrum import XpSampledSpectrum
from tests.files.paths import (con_ref_sampled_csv_path, con_ref_sampled_truncated_csv_path, mean_spectrum_avro_file,
                               mean_spectrum_csv_file, mean_spectrum_ecsv_file, mean_spectrum_fits_file,
                               mean_spectrum_xml_file, mean_spectrum_xml_plain_file)
from tests.test_converter.converter_paths import optimised_bases_df, converter_csv_solution_0_60_481_df
from tests.utils.utils import get_spectrum_with_source_id_and_xp, npt_array_err_message, is_instance_err_message

con_input_files = [mean_spectrum_avro_file, mean_spectrum_csv_file, mean_spectrum_ecsv_file, mean_spectrum_fits_file,
                   mean_spectrum_xml_file, mean_spectrum_xml_plain_file]

TOL = 4
_rtol, _atol = 1e-6, 1e-6  # Precision varies with extension


@pytest.fixture(scope='module')
def parser():
    yield InternalContinuousParser(MANDATORY_INPUT_COLS['convert'] + CORR_INPUT_COLUMNS)


@pytest.fixture(scope='module')
def sampled_parser():
    yield InternalSampledParser()


@pytest.fixture(scope='module')
def ref_sampled(sampled_parser):
    ref_sampled, _ = sampled_parser.parse_file(con_ref_sampled_csv_path)
    yield ref_sampled


@pytest.fixture(scope='module')
def ref_sampled_truncated(sampled_parser):
    ref_sampled_truncated, _ = sampled_parser.parse_file(con_ref_sampled_truncated_csv_path)
    yield ref_sampled_truncated


@pytest.fixture(scope='module')
def sampling():
    yield np.linspace(0, 60, 481)


@pytest.mark.parametrize('file', con_input_files)
def test_get_design_matrices(file, parser, sampling):
    instance = SampledBasisFunctions
    parsed_input, _ = parser.parse_file(file)
    design_matrices = get_design_matrices(sampling, optimised_bases_df)
    assert len(design_matrices) == 2
    assert list(design_matrices.keys()) == ['bp', 'rp']
    assert isinstance(design_matrices, dict), is_instance_err_message(file, dict)
    assert isinstance(design_matrices['bp'], instance), is_instance_err_message(file, instance)
    assert isinstance(design_matrices['rp'], instance), is_instance_err_message(file, instance)


@pytest.mark.parametrize('file', con_input_files)
def test_create_spectrum(file, sampling):
    spectrum = dict()
    truncation = True
    instance = XpSampledSpectrum
    parsed_input, _ = InputReader(file, convert, truncation).read()
    parsed_input_dict = parsed_input.to_dict('records')
    design_matrices = get_design_matrices(sampling, optimised_bases_df)
    for row in islice(parsed_input_dict, 1):  # Just the first row
        for band in BANDS:
            spectrum[band] = _create_spectrum(row, truncation, design_matrices, band)
    assert spectrum[BANDS.bp].get_source_id() == spectrum[BANDS.rp].get_source_id()
    for band in BANDS:
        assert isinstance(spectrum[band], instance), is_instance_err_message(file, instance, band)
        assert spectrum[band].get_xp() == band


@pytest.mark.parametrize('file', con_input_files)
def test_converter_both_types(file, sampling):
    converted_df, _ = convert(file, sampling=sampling, save_file=False)
    assert isinstance(converted_df, pd.DataFrame)
    assert len(converted_df) == 4
    pdt.assert_frame_equal(converted_df, converter_csv_solution_0_60_481_df, rtol=_rtol, atol=_atol)


@pytest.mark.parametrize('file', con_input_files)
def test_conversion(file, ref_sampled, sampling):
    converted_df, _ = convert(file, sampling=sampling, save_file=False)
    for spectrum in converted_df.to_dict('records'):
        ref = get_spectrum_with_source_id_and_xp(spectrum['source_id'], spectrum['xp'], ref_sampled)
        npt.assert_almost_equal(ref['flux'], spectrum['flux'], decimal=TOL)
        npt.assert_almost_equal(ref['error'], spectrum['flux_error'], decimal=TOL)


@pytest.mark.parametrize('file', con_input_files)
def test_truncation(file, ref_sampled_truncated, sampling):
    converted_truncated_df, _ = convert(file, sampling=sampling, truncation=True, save_file=False)
    for spectrum in converted_truncated_df.to_dict('records'):
        ref = get_spectrum_with_source_id_and_xp(spectrum['source_id'], spectrum['xp'], ref_sampled_truncated)
        npt.assert_almost_equal(ref['flux'], spectrum['flux'], decimal=TOL, err_msg=npt_array_err_message(file))
        npt.assert_almost_equal(ref['error'], spectrum['flux_error'], decimal=TOL, err_msg=npt_array_err_message(file))


@pytest.mark.parametrize('file', con_input_files)
@pytest.mark.parametrize('_sampling', [np.linspace(-15, 60, 600), np.linspace(-10, 71, 600),
                                       np.linspace(-11, 71, 600), None])
def test_sampling_error(file, _sampling):
    with pytest.raises(ValueError):
        convert(file, sampling=_sampling, save_file=False)


@pytest.mark.parametrize('file', con_input_files)
def test_sampling_equal(file, sampling):
    _, _positions = convert(file, sampling=sampling, truncation=True, save_file=False)
    npt.assert_array_equal(sampling, _positions)
