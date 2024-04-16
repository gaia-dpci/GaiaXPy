from os.path import join

from tests.files.paths import files_path

test_files_path = join(files_path, 'xp_continuous_c04')
regular_single_source_file = join(test_files_path, 'regular_single_source.avro')
no_corr_output_file = join(test_files_path, 'regular_single_source_converter_c04.csv')
with_corr_output_file = join(test_files_path, 'regular_single_source_converter_c04_with_corr.csv')
