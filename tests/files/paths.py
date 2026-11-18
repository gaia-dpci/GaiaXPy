"""
Root directories for test data.
"""
from pathlib import Path

files_path = Path(__file__).resolve().parent
input_files_path = files_path / 'input'
solution_path = files_path / 'solution'
config_path = files_path / 'config'
