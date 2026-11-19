import pandas as pd

from gaiaxpy.core.custom_errors import InvalidReleaseError
from gaiaxpy.core.generic_functions import get_function_name, _warning
from gaiaxpy.core.generic_variables import RELEASE_REDUNDANT_FUNCTIONS, RELEASES, n_params_dict, release_solution_id
from gaiaxpy.core.satellite import BANDS


def is_release_redundant(function):
    function_name = get_function_name(function)
    return function_name in RELEASE_REDUNDANT_FUNCTIONS


def parse_release(release):
    if release is None:
        return RELEASES.dr3
    if isinstance(release, str):
        release = release.lower()
    elif isinstance(release, list) and len(release) == 1:
        release = release[0].lower()
    if release in RELEASES:
        return release
    else:
        raise InvalidReleaseError(release)


def extract_solution_id(df):
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f'The input data is not a pandas DataFrame for type {type(df).__name__}.')

    columns = {'solution_id', 'solutionId'} & set(df.columns)
    if len(columns) == 0:
        raise ValueError("Expected either 'solution_id' or 'solutionId' column, but neither was found.")
    if len(columns) > 1:
        raise ValueError("Expected only one of 'solution_id' or 'solutionId', but both were found.")
    column = columns.pop()
    return df[column].unique().astype(str).tolist()


def _n_parameter_values(parsed_input_data, band):
    """Return the distinct non-null n-parameter values for one photometer."""
    column = f'{band}_n_parameters'
    return set(parsed_input_data[column].dropna().unique().tolist())


def _compatible_releases_from_n_parameters(parsed_input_data):
    """Return the releases compatible with the n-parameter values in the full input dataset."""
    required_columns = {'bp_n_parameters', 'rp_n_parameters'}
    missing = required_columns - set(parsed_input_data.columns)
    if missing:
        return None

    bp_values = _n_parameter_values(parsed_input_data, BANDS.bp)
    rp_values = _n_parameter_values(parsed_input_data, BANDS.rp)

    if not bp_values and not rp_values:
        raise ValueError('The input data contain no BP or RP parameters to process.')

    for band, values in ((BANDS.bp, bp_values), (BANDS.rp, rp_values)):
        if len(values) > 1:
            raise ValueError(f"The {band}_n_parameters column contains conflicting values: {sorted(values)}.")
        valid_values = {n_params_dict[release][band] for release in (RELEASES.dr3,)}
        invalid_values = values - valid_values
        if invalid_values:
            raise ValueError(f"The {band}_n_parameters values {sorted(invalid_values)} do not correspond to a known "
                             f"data release.")

    return {release for release in (RELEASES.dr3,)
            if (not bp_values or bp_values == {n_params_dict[release][BANDS.bp]})
            and (not rp_values or rp_values == {n_params_dict[release][BANDS.rp]})}


def get_release_from_data(parsed_input_data, function):
    if function is None:
        raise TypeError("The value of the 'function' parameter cannot be None")
    # These functions get their release from the operation/configuration, not from their input data.
    if is_release_redundant(function):
        return None

    has_solution_id = {'solution_id', 'solutionId'} & set(parsed_input_data.columns)

    if has_solution_id:
        data_solution_ids = set(extract_solution_id(parsed_input_data))
        known_solution_ids = {
            release: set(release_solution_id[release]) for release in (RELEASES.dr3,)
        }
        unknown_solution_ids = data_solution_ids - set().union(*known_solution_ids.values())
        if unknown_solution_ids:
            raise ValueError(
                f"The solution ID values {sorted(unknown_solution_ids)} do not correspond to a known data release."
            )

        matching_releases = {
            release for release, solution_ids in known_solution_ids.items()
            if data_solution_ids & solution_ids
        }
        if len(matching_releases) > 1:
            raise ValueError('The input data contain solution IDs from different data releases.')
        if len(matching_releases) == 1:
            return matching_releases.pop()
    else:
        _warning("The column 'solution_id' was not found in the input data, the release of the input data will be "
                 "determined from 'bp/rp_n_parameters'.")

    compatible_releases = _compatible_releases_from_n_parameters(parsed_input_data)
    if compatible_releases is None or len(compatible_releases) != 1:
        return None
    return compatible_releases.pop()


def check_release_matches_data(internal_phot_system, parsed_input_data, function, release=None):
    # All release values are standardised RELEASES (from Enum).
    release = parse_release(release)
    release_in_data = get_release_from_data(parsed_input_data, function)
    release_in_systems = set([s.value.get_release() for s in internal_phot_system])
    if len(release_in_systems) > 1:
        raise ValueError('The input systems correspond to different data releases. This is not allowed.')
    release_in_system = list(release_in_systems)[0]
    release_to_check = release_in_data or release
    if release_to_check != release_in_system:
        raise ValueError('The release of the input data does not match the release in systems. Both must correspond '
                         'to the same data release (DR3).')
    return release_to_check
