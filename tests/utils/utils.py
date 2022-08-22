import json
import numpy as np
import pandas as pd
from gaiaxpy.core.generic_functions import str_to_array


def parse_matrices(string):
    if len(string) == 0:
        return None
    else:
        return np.array(json.loads(string))

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


def df_columns_to_array(df, columns):
    for index, row in df.iterrows():
        for column in columns:
            df[column][index] = str_to_array(row[column])
    return df


def pos_file_to_array(pos_file):
    df = pd.read_csv(pos_file, float_precision='round_trip', converters={'pos': (lambda x: str_to_array(x))})
    return df['pos'].iloc[0]
