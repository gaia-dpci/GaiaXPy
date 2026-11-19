"""Small generic input files and general reference files."""
from tests.files.paths import input_files_path, solution_path

mini_path = input_files_path / 'mini_files'
mini_csv_file = mini_path / 'SPSS_mini.csv'
mini_fits_file = mini_path / 'XP_SPECTRA_RAW_mini.fits'
mini_xml_file = mini_path / 'XP_SPECTRA_RAW_mini.xml'
no_ext_file = mini_path / 'no_extension_file'

input_reader_solution_path = solution_path / 'input_reader_solution.csv'
output_sol_path = solution_path / 'output_solution'
