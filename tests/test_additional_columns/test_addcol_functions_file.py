import pandas as pd
import pandas.testing as pdt
import pytest

from gaiaxpy import (generate, PhotometricSystem, calibrate, convert, apply_error_correction,
                     get_inverse_covariance_matrix, get_inverse_square_root_covariance_matrix)
from gaiaxpy.file_parser.cast import _cast
from tests.files.paths import (mean_spectrum_avro_file, with_missing_bp_csv_file, with_missing_bp_ecsv_file,
                               with_missing_bp_fits_file, with_missing_bp_xml_file, with_missing_bp_xml_plain_file,
                               no_correction_solution_path)

ps = PhotometricSystem.Gaia_2
output_regular_avro = generate(mean_spectrum_avro_file, photometric_system=ps, save_file=False)


def test_generate_single_col_as_list_avro():
    output = generate(mean_spectrum_avro_file, photometric_system=ps, additional_columns=['sourceId'], save_file=False)
    original_src_id = output['source_id'].to_list()
    additional_src_id = output['sourceId'].to_list()
    assert original_src_id == additional_src_id
    output = output.drop(columns='sourceId')
    pdt.assert_frame_equal(output, output_regular_avro)


def test_generate_renaming_single_as_in_schema_avro():
    additional_columns = {'sol_id': 'solutionId'}
    output = generate(mean_spectrum_avro_file, photometric_system=ps, additional_columns=additional_columns,
                      save_file=False)
    assert all([value == 0 for value in output['sol_id'].values])
    output = output.drop(columns='sol_id')
    pdt.assert_frame_equal(output, output_regular_avro)


def test_generate_with_nueff_avro():
    additional_columns = {'nuEff': ['specShape', 'nuEff'], 'nuEffError': ['specShape', 'nuEffError']}
    output = generate(mean_spectrum_avro_file, photometric_system=ps, additional_columns=additional_columns,
                      save_file=False)
    assert all(output['nuEff'].values == [0.0011954542715102434, 0.0018434392986819148])
    assert all(output['nuEffError'].values == [1.309847448283108e-06, 2.04811312869424e-05])


def test_generate_with_nueff_avro_with_error_correction():
    additional_columns = {'nuEff': ['specShape', 'nuEff'], 'nuEffError': ['specShape', 'nuEffError']}
    output = generate(mean_spectrum_avro_file, photometric_system=ps, additional_columns=additional_columns,
                      error_correction=True, save_file=False)
    assert all(output['nuEff'].values == [0.0011954542715102434, 0.0018434392986819148])
    assert all(output['nuEffError'].values == [1.309847448283108e-06, 2.04811312869424e-05])


def test_generate_other_formats():
    key = 'sol_id'
    additional_columns = {key: 'solution_id'}
    solution = pd.read_csv(no_correction_solution_path)
    solution = solution.drop(columns=[c for c in solution.columns if c != 'source_id' and 'Sdss_' not in c and
                                      'Stromgren_' not in c])
    for file in (with_missing_bp_csv_file, with_missing_bp_ecsv_file, with_missing_bp_fits_file,
                 with_missing_bp_xml_file, with_missing_bp_xml_plain_file):
        output = generate(file, photometric_system=[PhotometricSystem.SDSS, PhotometricSystem.Stromgren],
                          additional_columns=additional_columns, error_correction=True, save_file=False)
        assert all(output[key].values == [4545469030156206080, 4545469030156206081, 4545469030156206080])
        output = output.drop(columns=[key])
        pdt.assert_frame_equal(output, _cast(solution))


def test_not_implemented_functions():
    for function in [calibrate, convert, apply_error_correction, get_inverse_covariance_matrix,
                     get_inverse_square_root_covariance_matrix]:
        additional_columns = 'bp_coefficients'
        with pytest.raises(TypeError):
            function(mean_spectrum_avro_file, additional_columns=additional_columns, save_file=False)
