import numpy.testing as npt
import pandas as pd
import pytest
from numpy import ndarray, dtype

from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS
from tests.files.paths import (mean_spectrum_avro_file, mean_spectrum_csv_file, mean_spectrum_ecsv_file,
                               mean_spectrum_fits_file, mean_spectrum_xml_file, mean_spectrum_xml_plain_file)
from tests.utils.utils import get_spectrum_with_source_id

parser = InternalContinuousParser(MANDATORY_INPUT_COLS['calibrate'] + CORR_INPUT_COLUMNS)


type_map = {'source_id': pd.Int64Dtype(),
            'solution_id': pd.Int64Dtype(),
            f'{BANDS.rp}_n_parameters': pd.Int16Dtype(),
            f'{BANDS.bp}_n_parameters': pd.Int16Dtype(),
            f'{BANDS.rp}_n_rejected_measurements': pd.Int64Dtype(),
            f'{BANDS.bp}_n_rejected_measurements': pd.Int64Dtype(),
            f'{BANDS.rp}_n_measurements': pd.Int64Dtype(),
            f'{BANDS.bp}_n_measurements': pd.Int64Dtype(),
            f'{BANDS.rp}_standard_deviation': pd.Float64Dtype(),
            f'{BANDS.bp}_standard_deviation': pd.Float64Dtype(),
            f'{BANDS.rp}_num_of_transits': pd.Int64Dtype(),
            f'{BANDS.bp}_num_of_transits': pd.Int64Dtype(),
            f'{BANDS.rp}_num_of_blended_transits': pd.Int64Dtype(),
            f'{BANDS.bp}_num_of_blended_transits': pd.Int64Dtype(),
            f'{BANDS.rp}_num_of_contaminated_transits': pd.Int64Dtype(),
            f'{BANDS.bp}_num_of_contaminated_transits': pd.Int64Dtype(),
            f'{BANDS.rp}_coefficients': dtype('O'),
            f'{BANDS.bp}_coefficients': dtype('O'),
            f'{BANDS.rp}_coefficient_covariances': dtype('O'),
            f'{BANDS.bp}_coefficient_covariances': dtype('O'),
            f'{BANDS.rp}_degrees_of_freedom': pd.Int64Dtype(),
            f'{BANDS.bp}_degrees_of_freedom': pd.Int64Dtype(),
            f'{BANDS.rp}_n_relevant_bases': pd.Int64Dtype(),
            f'{BANDS.bp}_n_relevant_bases': pd.Int64Dtype(),
            f'{BANDS.rp}_basis_function_id': pd.Int64Dtype(),
            f'{BANDS.bp}_basis_function_id': pd.Int64Dtype(),
            f'{BANDS.rp}_chi_squared': pd.Float64Dtype(),
            f'{BANDS.bp}_chi_squared': pd.Float64Dtype(),
            f'{BANDS.rp}_coefficient_errors': dtype('O'),
            f'{BANDS.bp}_coefficient_errors': dtype('O'),
            f'{BANDS.rp}_coefficient_correlations': dtype('O'),
            f'{BANDS.bp}_coefficient_correlations': dtype('O'),
            f'{BANDS.rp}_relative_shrinking': pd.Float64Dtype(),
            f'{BANDS.bp}_relative_shrinking': pd.Float64Dtype(),
            f'{BANDS.bp}_covariance_matrix': dtype('O'),
            f'{BANDS.rp}_covariance_matrix': dtype('O')}


@pytest.mark.parametrize('file', [mean_spectrum_avro_file, mean_spectrum_csv_file, mean_spectrum_ecsv_file,
                                  mean_spectrum_fits_file, mean_spectrum_xml_file, mean_spectrum_xml_plain_file])
def test_parse_returns_dataframe(file):
    parsed_file, _ = parser.parse_file(file)
    assert isinstance(parsed_file, pd.DataFrame)


@pytest.mark.parametrize('file', [mean_spectrum_avro_file, mean_spectrum_csv_file, mean_spectrum_ecsv_file,
                                  mean_spectrum_fits_file, mean_spectrum_xml_file, mean_spectrum_xml_plain_file])
def test_column_types(file):
    parsed_file, _ = parser.parse_file(file)
    actual_dtypes = dict(zip(parsed_file.columns, parsed_file.dtypes))
    for key in actual_dtypes.keys():
        assert actual_dtypes[key] == type_map[key],\
            f'Key {key} actual type is {actual_dtypes[key]} but expected type is {type_map[key]} for file {file}.'


@pytest.mark.parametrize('file', [mean_spectrum_csv_file, mean_spectrum_ecsv_file, mean_spectrum_fits_file,
                                  mean_spectrum_xml_file, mean_spectrum_xml_plain_file])
def test_coefficients_types(file):
    parsed_file, _ = parser.parse_file(file)
    for band in BANDS:
        assert isinstance(parsed_file[f'{band}_coefficients'][0], ndarray)
        assert isinstance(parsed_file[f'{band}_coefficient_errors'][0], ndarray)
        assert isinstance(parsed_file[f'{band}_coefficient_correlations'][0], ndarray)


# The column 'xp_coefficient_correlations' should be a matrix of size 'bp_num_of_parameters'^2
@pytest.mark.parametrize('file', [mean_spectrum_csv_file, mean_spectrum_ecsv_file, mean_spectrum_fits_file,
                                  mean_spectrum_xml_file, mean_spectrum_xml_plain_file])
def test_coefficient_correlations_is_matrix(file):
    parsed_file, _ = parser.parse_file(file)
    for band in BANDS:
        assert isinstance(parsed_file[f'{band}_coefficient_correlations'][0][0], ndarray)
        assert len(parsed_file[f'{band}_coefficient_correlations'][0][0]) == parsed_file[f'{band}_n_parameters'][0]


# AVRO
def test_column_names():
    parsed_avro_file, _ = parser.parse_file(mean_spectrum_avro_file)
    assert list(parsed_avro_file.columns) == ['source_id', f'{BANDS.rp}_n_rejected_measurements',
                                              f'{BANDS.rp}_chi_squared', f'{BANDS.rp}_degrees_of_freedom',
                                              f'{BANDS.rp}_n_parameters', f'{BANDS.rp}_standard_deviation',
                                              f'{BANDS.rp}_n_measurements', f'{BANDS.rp}_n_relevant_bases',
                                              f'{BANDS.rp}_basis_function_id', f'{BANDS.rp}_num_of_transits',
                                              f'{BANDS.bp}_n_rejected_measurements', f'{BANDS.bp}_chi_squared',
                                              f'{BANDS.bp}_degrees_of_freedom', f'{BANDS.bp}_n_parameters',
                                              f'{BANDS.bp}_standard_deviation', f'{BANDS.bp}_n_measurements',
                                              f'{BANDS.bp}_n_relevant_bases', f'{BANDS.bp}_basis_function_id',
                                              f'{BANDS.rp}_num_of_blended_transits', f'{BANDS.bp}_num_of_transits',
                                              f'{BANDS.bp}_num_of_contaminated_transits',
                                              f'{BANDS.rp}_num_of_contaminated_transits',
                                              f'{BANDS.bp}_num_of_blended_transits', 'solution_id',
                                              f'{BANDS.rp}_coefficient_covariances', f'{BANDS.rp}_coefficients',
                                              f'{BANDS.bp}_coefficient_covariances', f'{BANDS.bp}_coefficients',
                                              f'{BANDS.bp}_covariance_matrix', f'{BANDS.rp}_covariance_matrix']


def test_coefficients_types_avro():
    parsed_avro_file, _ = parser.parse_file(mean_spectrum_avro_file)
    for band in BANDS:
        assert isinstance(parsed_avro_file[f'{band}_coefficients'][0], ndarray)
        assert isinstance(parsed_avro_file[f'{band}_coefficient_covariances'][0], ndarray)


# The column 'xp_coefficient_covariances' should be a matrix of size 'bp_num_of_parameters'^2
def test_coefficient_covariances_is_matrix():
    parsed_avro_file, _ = parser.parse_file(mean_spectrum_avro_file)
    for band in BANDS:
        assert isinstance(parsed_avro_file[f'{band}_coefficient_covariances'][0][0], ndarray)
        assert (len(parsed_avro_file[f'{band}_coefficient_covariances'][0][0]) ==
                parsed_avro_file[f'{band}_n_parameters'][0])


def test_parse_equality():
    parsed_csv_file, _ = parser.parse_file(mean_spectrum_csv_file)
    parsed_fits_file, _ = parser.parse_file(mean_spectrum_fits_file)
    parsed_plain_xml_file, _ = parser.parse_file(mean_spectrum_xml_plain_file)
    parsed_xml_file, _ = parser.parse_file(mean_spectrum_xml_file)
    source_ids = parsed_csv_file['source_id'].to_list()
    for source_id in source_ids:
        csv_data = get_spectrum_with_source_id(source_id, parsed_csv_file)
        fits_data = get_spectrum_with_source_id(source_id, parsed_fits_file)
        plain_xml_data = get_spectrum_with_source_id(source_id, parsed_plain_xml_file)
        xml_data = get_spectrum_with_source_id(source_id, parsed_xml_file)
        assert csv_data.keys() == fits_data.keys()
        assert fits_data.keys() == plain_xml_data.keys()
        assert plain_xml_data.keys() == xml_data.keys()
        for key in csv_data.keys():
            decimal = 2 if key in ['bp_covariance_matrix', 'rp_covariance_matrix'] else 4
            npt.assert_almost_equal(csv_data[key], fits_data[key], decimal=decimal)  # Precision varies across formats
            npt.assert_almost_equal(fits_data[key], plain_xml_data[key], decimal=decimal)
            npt.assert_almost_equal(plain_xml_data[key], xml_data[key], decimal=decimal)
