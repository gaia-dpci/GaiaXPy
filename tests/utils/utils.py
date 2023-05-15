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
