import pandas.testing as pdt

from gaiaxpy import generate, PhotometricSystem
from tests.files.paths import mean_spectrum_avro_file

'''
def test_single_col_as_list():
    ps = PhotometricSystem.Gaia_2
    output = generate(mean_spectrum_avro_file, photometric_system=ps, additional_columns=['source_id'], save_file=False)
    output_regular = generate(mean_spectrum_avro_file, photometric_system=ps, save_file=False)
    pdt.assert_frame_equal(output, output_regular)
'''


def test_renaming_single_as_in_schema():
    ps = PhotometricSystem.Gaia_2
    additional_columns = {'sol_id': 'solutionId'}
    output = generate(mean_spectrum_avro_file, photometric_system=ps, additional_columns=additional_columns,
                      save_file=False)
    output_regular = generate(mean_spectrum_avro_file, photometric_system=ps, save_file=False)
    pdt.assert_frame_equal(output, output_regular)


'''
def test_with_nueff():
    additional_columns = {'nuEff': ['specShape', 'nuEff'], 'nuEffError': ['specShape', 'nuEffError']}
    ps = PhotometricSystem.Gaia_2
    output = generate(mean_spectrum_avro_file, photometric_system=ps, additional_columns=additional_columns,
                      save_file=False)
'''