import numpy as np
import pandas as pd

# Avoid warning, false positive
pd.options.mode.chained_assignment = None


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
            df[column][index] = np.fromstring(row[column][1:-1], sep=',')
    return df


def pos_file_to_array(pos_file):
    df = pd.read_csv(pos_file, float_precision='round_trip')
    return np.fromstring(df['pos'].iloc[0][1:-1], sep=',')
