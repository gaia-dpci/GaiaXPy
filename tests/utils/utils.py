import json

import numpy as np
import pandas as pd
import pytest

from gaiaxpy.core.generic_functions import str_to_array

_rtol, _atol = 1e-7, 1e-7


def parse_matrices(string):
    return None if len(string) == 0 else np.array(json.loads(string))


def get_spectrum_with_source_id(source_id, spectra):
    if isinstance(spectra, list):
        for spectrum in spectra:
            if spectrum.get_source_id() == source_id:
                return spectrum
    elif isinstance(spectra, pd.DataFrame):
        return spectra.loc[spectra['source_id'] == source_id].to_dict('records')[0]
    raise ValueError('Spectrum does not exist or function is not defined for variable spectra type.')


def get_spectrum_with_source_id_and_xp(source_id, xp, spectra):
    if isinstance(spectra, list):
        for spectrum in spectra:
            if spectrum.get_source_id() == source_id and spectrum.get_xp() == xp:
                return spectrum
    elif isinstance(spectra, pd.DataFrame):
        return spectra.loc[(spectra['source_id'] == source_id) & (spectra['xp'] == xp.upper())].to_dict('records')[0]
    raise ValueError('Spectrum does not exist or function is not defined for variable spectra type.')


def pos_file_to_array(pos_file):
    df = pd.read_csv(pos_file, float_precision='round_trip', converters={'pos': (lambda x: str_to_array(x))})
    return df['pos'].iloc[0]


def custom_void_array_comparison(df_computed, df_solution, column: str, dtypes: list):
    """
    Used by line finder functionality. Arrays contain elements of different types, and regular comparison fails.
    """
    if len(df_computed) != len(df_solution):
        raise ValueError('Lengths of DataFrames are different.')
    df_computed_lines = df_computed[column].values
    df_solution_lines = df_solution[column].values
    for computed_lines, solution_lines in zip(df_computed_lines, df_solution_lines):
        if len(computed_lines) == len(solution_lines):
            for computed_line, solution_line in zip(computed_lines, solution_lines):
                # Convert line to dictionary
                d1 = {key: computed_line[key] for key, _ in dtypes}
                d2 = {key: solution_line[key] for key, _ in dtypes}
                line_name1 = d1.pop('line_name')
                line_name2 = d2.pop('line_name')
                assert line_name1 == line_name2
                assert d1 == pytest.approx(d2, rel=_rtol, abs=_atol, nan_ok=True)
        else:
            raise ValueError('Lengths of internal lines are different.')


# Define the converter function
def str_to_array_rec(input_str, dtypes):
    lst = eval(input_str)
    lst = [tuple(element) for element in lst]
    output = [np.array(line, dtype=dtypes) for line in lst]
    return np.array(output)


def get_converters(columns, dtypes=None):
    if isinstance(columns, str):
        return {columns: lambda x: str_to_array_rec(x, dtypes)}
    elif isinstance(columns, list):
        if len(columns) == 1:
            return {columns[0]: lambda x: str_to_array_rec(x, dtypes)}
        elif len(columns) > 1:  # Extrema BP and RP case
            return {column: lambda x: str_to_array(x) for column in columns}
    raise ValueError("Input doesn't correspond to any of the expected types.")
