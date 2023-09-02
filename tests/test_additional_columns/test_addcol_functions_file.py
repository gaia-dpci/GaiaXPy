import pandas.testing as pdt
import pytest

from gaiaxpy import generate, PhotometricSystem, calibrate, convert, apply_error_correction, \
    get_inverse_covariance_matrix, get_inverse_square_root_covariance_matrix
from tests.files.paths import mean_spectrum_avro_file


ps = PhotometricSystem.Gaia_2
output_regular = generate(mean_spectrum_avro_file, photometric_system=ps, save_file=False)

# Generate
def test_single_col_as_list():
    output = generate(mean_spectrum_avro_file, photometric_system=ps, additional_columns=['sourceId'], save_file=False)
    original_src_id = output['source_id'].to_list()
    additional_src_id = output['sourceId'].to_list()
    assert original_src_id == additional_src_id
    output = output.drop(columns='sourceId')
    pdt.assert_frame_equal(output, output_regular)

def test_renaming_single_as_in_schema():
    additional_columns = {'sol_id': 'solutionId'}
    output = generate(mean_spectrum_avro_file, photometric_system=ps, additional_columns=additional_columns,
                      save_file=False)
    assert all([value == 0 for value in output['sol_id'].values])
    output = output.drop(columns='sol_id')
    pdt.assert_frame_equal(output, output_regular)

def test_with_nueff():
    additional_columns = {'nuEff': ['specShape', 'nuEff'], 'nuEffError': ['specShape', 'nuEffError']}
    output = generate(mean_spectrum_avro_file, photometric_system=ps, additional_columns=additional_columns,
                      save_file=False)
    assert all(output['nuEff'].values == [0.0011954542715102434, 0.0018434392986819148])
    assert all(output['nuEffError'].values == [1.309847448283108e-06, 2.04811312869424e-05])


# get_inverse_covariance_matrix, get_inverse_square_root_covariance_matrix
def test_not_implemented():
    for function in [calibrate, convert, apply_error_correction, get_inverse_covariance_matrix,
                     get_inverse_square_root_covariance_matrix]:
        additional_columns = 'bp_coefficients'
        with pytest.raises(TypeError):
            function(mean_spectrum_avro_file, additional_columns=additional_columns, save_file=False)
