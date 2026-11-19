import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import (generate, PhotometricSystem, calibrate, convert, apply_error_correction,
                     get_inverse_covariance_matrix, get_inverse_square_root_covariance_matrix)
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.file_parser.cast import _cast
from tests.files.continuous import (dr3_mean_spectra_avro_file, dr3_with_missing_bp_csv_file,
                                    dr3_with_missing_bp_ecsv_file, dr3_with_missing_bp_fits_file,
                                    dr3_with_missing_bp_xml_binary_file, dr3_with_missing_bp_xml_plain_file)
from tests.files.generator import no_correction_solution_path

ps = PhotometricSystem.DR3_Gaia_2


@pytest.fixture
def output_regular_avro():
    return generate(dr3_mean_spectra_avro_file, photometric_system=ps, save_file=False)


def test_generate_single_col_as_list_avro(output_regular_avro):
    output = generate(dr3_mean_spectra_avro_file, photometric_system=ps, additional_columns=['sourceId'],
                      save_file=False)
    original_src_id = output['source_id'].to_list()
    additional_src_id = output['sourceId'].to_list()
    assert original_src_id == additional_src_id
    output = output.drop(columns='sourceId')
    pdt.assert_frame_equal(output, output_regular_avro)


def test_generate_renaming_single_as_in_schema_avro(output_regular_avro):
    additional_columns = {'sol_id': 'solutionId'}
    output = generate(dr3_mean_spectra_avro_file, photometric_system=ps, additional_columns=additional_columns,
                      save_file=False)
    assert all([value == 4545469030156206080 for value in output['sol_id'].values])
    output = output.drop(columns='sol_id')
    pdt.assert_frame_equal(output, output_regular_avro)


def test_generate_with_nueff_avro():
    additional_columns = {'nuEff': ['specShape', 'nuEff'], 'nuEffError': ['specShape', 'nuEffError']}
    output = generate(dr3_mean_spectra_avro_file, photometric_system=ps, additional_columns=additional_columns,
                      save_file=False)
    assert all(output['nuEff'].values == [0.0011954542715102434, 0.0018434392986819148])
    assert all(output['nuEffError'].values == [1.309847448283108e-06, 2.04811312869424e-05])


def test_generate_with_nueff_avro_with_error_correction():
    additional_columns = {'nuEff': ['specShape', 'nuEff'], 'nuEffError': ['specShape', 'nuEffError']}
    output = generate(dr3_mean_spectra_avro_file, photometric_system=ps, additional_columns=additional_columns,
                      error_correction=True, save_file=False)
    assert all(output['nuEff'].values == [0.0011954542715102434, 0.0018434392986819148])
    assert all(output['nuEffError'].values == [1.309847448283108e-06, 2.04811312869424e-05])


def test_generate_other_formats():
    key = 'bf_dof'
    additional_columns = {key: 'bp_degrees_of_freedom'}
    solution = pd.read_csv(no_correction_solution_path, **CSV_FLOAT_PRECISION_KWARGS)
    solution = solution.drop(columns=[c for c in solution.columns if c != 'source_id' and 'DR3_Sdss_' not in c and
                                      'DR3_Stromgren_' not in c])
    for file in (dr3_with_missing_bp_csv_file, dr3_with_missing_bp_ecsv_file, dr3_with_missing_bp_fits_file,
                 dr3_with_missing_bp_xml_binary_file, dr3_with_missing_bp_xml_plain_file):
        output = generate(file, photometric_system=[PhotometricSystem.DR3_SDSS, PhotometricSystem.DR3_Stromgren],
                          additional_columns=additional_columns, error_correction=True, save_file=False)
        # Inferred as float instead of in due to nan value
        np.testing.assert_equal(output[key].values, np.array([4646.0, np.nan, 2320.0]))
        output = output.drop(columns=[key])
        pdt.assert_frame_equal(output, _cast(solution))


def test_not_implemented_functions():
    for function in [calibrate, convert, apply_error_correction, get_inverse_covariance_matrix,
                     get_inverse_square_root_covariance_matrix]:
        additional_columns = 'bp_coefficients'
        with pytest.raises(TypeError):
            function(dr3_mean_spectra_avro_file, additional_columns=additional_columns, save_file=False)
