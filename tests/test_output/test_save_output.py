import unittest
import numpy as np
import pandas as pd
import subprocess
from os.path import join
from tests.files import files_path
from gaiaxpy import calibrate, convert, generate, PhotometricSystem, \
                    simulate_continuous, simulate_sampled

mean_spectrum = join(files_path, 'xp_continuous', 'XP_CONTINUOUS_RAW_dr3int6.csv')
mini_path = join(files_path, 'mini_files')
spss_file = join(mini_path, 'SPSS_mini.csv')
# Create output folder
output_path = 'tests_output_files'

# Load md5sums of the expected output files
md5sum_path = join(files_path, 'md5sum_output_files.csv')
solution_md5sum_df = pd.read_csv(md5sum_path, float_precision='round_trip')

# TODO: AVRO cannot be tested by md5sum

def get_sampling_and_filename(prefix, start, step, stop):
    return np.linspace(start, step, stop), f'{prefix}_{start}_{step}_{stop}'

def generate_current_md5sum_df(output_path):
    # Generate dataframe with md5sum of current files
    command_string = f"md5sum {join(output_path, '*')}"
    command = subprocess.Popen(command_string, shell=True, stdout=subprocess.PIPE)
    command_output, error = command.communicate()
    command_output = command_output.split()
    hashes = [element for index, element in enumerate(command_output) if index % 2 == 0]
    names = [element.decode('utf-8').split('/')[1] for index, element in enumerate(command_output) if index % 2 != 0]
    actual_md5sum_df = pd.DataFrame(data={'hash': hashes, 'filename': names})
    return actual_md5sum_df


class TestSaveOutput(unittest.TestCase):
    """
    This class generates the output files of every tool
    in the package. These files need to be 'manually'
    compared with the output files of the previous version of
    the package in order to guarantee that they are still the same.
    """
    def test_save_output_calibrator(self):
        filename = 'calibrator'; output_formats = ['csv', 'fits', 'xml', 'avro']
        for format in output_formats:
            calibrate(mean_spectrum, save_path=output_path, output_file=filename, output_format=format)
        # Generate dataframe with md5sum of current files
        actual_md5sum_df = generate_current_md5sum_df(output_path)
        # Test all but avro because it is a binary format and the md5sum maybe different even if the files have the same contents
        for format in output_formats[:-2]: # XML changes whenever the file is generated and AVRO is a binary format
            # Look for the name of the file in the md5sum data
            file = f'{filename}.{format}'
            expected_md5sum = solution_md5sum_df.loc[solution_md5sum_df['filename'] == file]['hash'].iloc[0]
            actual_md5sum = actual_md5sum_df.loc[actual_md5sum_df['filename'] == file]['hash'].iloc[0]
            self.assertEqual(expected_md5sum, actual_md5sum.decode('utf8'))
        # Test sampling file (only possible for csv, as avro is binary)
        sampling_file = f'{filename}_sampling.csv'
        expected_md5sum = solution_md5sum_df.loc[solution_md5sum_df['filename'] == sampling_file]['hash'].iloc[0]
        actual_md5sum = actual_md5sum_df.loc[actual_md5sum_df['filename'] == sampling_file]['hash'].iloc[0]
        self.assertEqual(expected_md5sum, actual_md5sum.decode('utf8'))

    def test_save_output_generator(self):
        phot_systems = [PhotometricSystem.Gaia_2, PhotometricSystem.SDSS_Std, \
                        PhotometricSystem.Gaia_DR3_Vega]
        ph = 'photometry_'
        filenames = [f'{ph}gaia_ab', f'{ph}sdss_doi', f'{ph}gaia_vega']
        output_formats = ['csv', 'csv', 'fits']
        for system, filename, format in zip(phot_systems, filenames, output_formats):
            generate(mean_spectrum, system, save_path=output_path, output_file=filename, output_format=format)
        # Generate dataframe with md5sum of current files
        actual_md5sum_df = generate_current_md5sum_df(output_path)
        for filename, format in zip(filenames, output_formats):
            expected_md5sum = solution_md5sum_df.loc[solution_md5sum_df['filename'] == f'{filename}.{format}']['hash'].iloc[0]
            actual_md5sum = actual_md5sum_df.loc[actual_md5sum_df['filename'] == f'{filename}.{format}']['hash'].iloc[0]
            self.assertEqual(expected_md5sum, actual_md5sum.decode('utf8'))

    def test_save_output_converter(self):
        filenames = []
        c = 'converter'
        # Basis CSV conversion
        convert(mean_spectrum, output_file=join(output_path, c), output_format='csv')
        filenames.append(c)
        # Custom sampling conversions
        output_formats = ['csv', 'fits', 'xml']
        samplings = [(0, 40, 350), (0, 45, 400), (0, 30, 300)]
        for values, format in zip(samplings, output_formats):
            sampling, filename = get_sampling_and_filename(f'{c}_custom', *values)
            convert(mean_spectrum, sampling=sampling, save_path=output_path, output_file=filename, output_format=format)
            filenames.append(filename)
        # Insert format of initial basic convert
        output_formats.insert(0, 'csv')
        # Generate dataframe with md5sum of current files
        actual_md5sum_df = generate_current_md5sum_df(output_path)
        for filename, format in zip(filenames, output_formats):
            expected_md5sum = solution_md5sum_df.loc[solution_md5sum_df['filename'] == f'{filename}.{format}']['hash'].iloc[0]
            actual_md5sum = actual_md5sum_df.loc[actual_md5sum_df['filename'] == f'{filename}.{format}']['hash'].iloc[0]
            self.assertEqual(expected_md5sum, actual_md5sum.decode('utf8'))

        # Test sampling file (only possible for csv, as avro is binary), basic conversion
        def test_save_output_converter_sampling(self):
            sampling_file = f'{c}_sampling.csv'
            expected_md5sum = solution_md5sum_df.loc[solution_md5sum_df['filename'] == sampling_file]['hash'].iloc[0]
            actual_md5sum = actual_md5sum_df.loc[actual_md5sum_df['filename'] == sampling_file]['hash'].iloc[0]
            self.assertEqual(expected_md5sum, actual_md5sum.decode('utf8'))

        def test_save_output_converter_custom_sampling(self):
            sampling_file = f'{c}_custom_0_40_350_sampling.csv'
            expected_md5sum = solution_md5sum_df.loc[solution_md5sum_df['filename'] == sampling_file]['hash'].iloc[0]
            actual_md5sum = actual_md5sum_df.loc[actual_md5sum_df['filename'] == sampling_file]['hash'].iloc[0]
            self.assertEqual(expected_md5sum, actual_md5sum.decode('utf8'))

    def test_save_output_simulator_sampled(self):
        filename = 'simulator_sampled'
        simulate_sampled(spss_file, save_file=True, sampling=np.linspace(0, 60, 300), save_path=output_path, output_file=filename)
        actual_md5sum_df = generate_current_md5sum_df(output_path)
        filename_str = f'{filename}.csv'
        sampling_str = f'{filename}_sampling.csv'
        # Test data
        expected_md5sum = solution_md5sum_df.loc[solution_md5sum_df['filename'] == filename_str]['hash'].iloc[0]
        actual_md5sum = actual_md5sum_df.loc[actual_md5sum_df['filename'] == filename_str]['hash'].iloc[0]
        self.assertEqual(expected_md5sum, actual_md5sum.decode('utf8'))
        # Test sampling
        expected_md5sum = solution_md5sum_df.loc[solution_md5sum_df['filename'] == sampling_str]['hash'].iloc[0]
        actual_md5sum = actual_md5sum_df.loc[actual_md5sum_df['filename'] == sampling_str]['hash'].iloc[0]
        self.assertEqual(expected_md5sum, actual_md5sum.decode('utf8'))

    def test_save_output_simulator_continuous(self):
        filename = 'simulator_continuous'
        simulate_continuous(spss_file, save_file=True, save_path=output_path, output_file=filename)
        actual_md5sum_df = generate_current_md5sum_df(output_path)
        filename_str = f'{filename}.csv'
        # Test data
        expected_md5sum = solution_md5sum_df.loc[solution_md5sum_df['filename'] == filename_str]['hash'].iloc[0]
        actual_md5sum = actual_md5sum_df.loc[actual_md5sum_df['filename'] == filename_str]['hash'].iloc[0]
        self.assertEqual(expected_md5sum, actual_md5sum.decode('utf8'))
