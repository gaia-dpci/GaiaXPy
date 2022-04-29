import subprocess
import pandas as pd
from os.path import join

def generate_current_md5sum_df(output_path):
    # Generate DataFrame with md5sum of current files
    command_string = f"md5sum {join(output_path, '*')}"
    command = subprocess.Popen(command_string, shell=True, stdout=subprocess.PIPE)
    command_output, error = command.communicate()
    command_output = command_output.split()
    hashes = [element for index, element in enumerate(command_output) if index % 2 == 0]
    names = [element.decode('utf-8').split('/')[1] for index, element in enumerate(command_output) if index % 2 != 0]
    current_md5sum_df = pd.DataFrame(data={'hash': hashes, 'filename': names})
    return current_md5sum_df
