"""Select BP/RP basis definitions and evaluate the converter design matrices.

DR3 configurations contain Hermite functions. Each evaluated matrix has one
row per basis function and one column per pseudo-wavelength sample.
It is stored in a SampledBasisFunctions object.
"""
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions


def __convert_to_dict(obj):
    """Convert parser Tuple objects and attribute containers to nested dictionaries.

    Args:
        obj (object): Value to convert. Objects whose class is named 'Tuple' are
            read through _asdict(); other objects with __dict__ use their attributes.

    Returns:
        dict or object: Recursively converted fields for those objects. Other
        values, including ordinary lists and dictionaries, are returned unchanged.
    """
    if obj.__class__.__name__ == 'Tuple':
        return {key: __convert_to_dict(val) for key, val in obj._asdict().items()}
    elif hasattr(obj, '__dict__'):
        return {key: __convert_to_dict(val) for key, val in obj.__dict__.items()}
    else:
        return obj


def get_unique_id(config: 'pd.DataFrame', _id: int) -> 'pd.DataFrame':
    """Select all configuration rows with the requested uniqueId value.

    Args:
        config (pandas.DataFrame): Configuration table containing uniqueId.
        _id (int): Basis-configuration identifier to match.

    Returns:
        pandas.DataFrame: Matching rows with their existing columns and index.
        If there is no match, the result is empty.

    Raises:
        KeyError: The table has no uniqueId column.
    """
    return config.loc[config['uniqueId'] == _id]


def _get_transposed_design_matrix(sampling: 'np.ndarray', bases_config, band: str) -> SampledBasisFunctions:
    """Evaluate the selected photometer's bases on a pseudo-wavelength grid.

    Args:
        sampling (numpy.ndarray): One-dimensional pseudo-wavelength positions.
        bases_config (object): Parsed configuration containing the DR3 hermiteFunction fields.
        band (str): Lowercase 'bp' or 'rp', selecting the corresponding configuration.

    Returns:
        SampledBasisFunctions: Supplied grid and a design matrix with shape
        (n_bases, n_samples), including the configured basis transformation.

    Raises:
        ValueError: The configuration layout is unsupported.

    Notes:
        The basis evaluator reports missing configuration fields and incompatible
        matrix dimensions to the caller.
    """
    bands_config = get_bands_config(bases_config)
    band_config = bands_config.bpConfig if band == BANDS.bp else bands_config.rpConfig
    band_config_dict = {field: getattr(band_config, field) for field in band_config._fields}

    from pandas import DataFrame as pdDf
    config_df = pdDf.from_dict({band: band_config_dict}, orient='index')
    return SampledBasisFunctions.from_config(sampling, config_df)


def get_transposed_design_matrices(sampling: 'np.ndarray', bases_config: 'pd.DataFrame') -> dict:
    """Evaluate both photometers' bases on the same pseudo-wavelength grid.

    Args:
        sampling (numpy.ndarray): One-dimensional pseudo-wavelength positions.
        bases_config (object): Parsed Hermite configuration with BP and RP definitions.

    Returns:
        dict[str, SampledBasisFunctions]: Objects keyed by 'bp' and 'rp'. Each
        stores the sampling grid and its basis-by-sample matrix.

    Raises:
        ValueError: The configuration layout is unsupported.
    """
    return {band: _get_transposed_design_matrix(sampling, bases_config, band) for band in BANDS}


def get_bands_config(bases_config):
    """Find the BP/RP definitions in a supported parsed basis configuration.

    Args:
        bases_config (object): DR3 configuration with hermiteFunction.

    Returns:
        object: Configuration object exposing bpConfig and rpConfig.

    Raises:
        ValueError: Neither supported top-level field is present.
        AttributeError: A basisDefinition field is present but has no spline field.
    """
    if hasattr(bases_config, 'hermiteFunction'):
        return bases_config.hermiteFunction
    else:
        raise ValueError('Bases configuration type not implemented.')
