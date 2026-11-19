"""Define reader columns and describe the inputs of public GaiaXPy functions.

Internal requirement tables are shared by file, DataFrame and Archive readers.
The public get_required_columns helper describes local table inputs without
reading data or contacting the Archive.
"""

from copy import deepcopy
from dataclasses import dataclass, field
from inspect import isfunction
from textwrap import fill

from gaiaxpy.core.satellite import BANDS

__CAL_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'bp_coefficients', 'bp_standard_deviation',
                        'rp_n_parameters', 'rp_coefficients', 'rp_standard_deviation']
__CON_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'bp_coefficients', 'bp_standard_deviation',
                        'rp_n_parameters', 'rp_coefficients', 'rp_standard_deviation']
__GEN_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'bp_coefficients', 'bp_standard_deviation',
                        'rp_n_parameters', 'rp_coefficients', 'rp_standard_deviation']
__INV_MANDATORY_COLS = ['source_id', 'bp_n_parameters', 'bp_coefficients', 'bp_standard_deviation',
                        'rp_n_parameters', 'rp_coefficients', 'rp_standard_deviation']

COV_INPUT_COLUMNS = ['bp_coefficient_covariances', 'rp_coefficient_covariances']
CORR_INPUT_COLUMNS = ['bp_coefficient_errors', 'bp_coefficient_correlations', 'rp_coefficient_errors',
                      'rp_coefficient_correlations']

MANDATORY_INPUT_COLS = {'_apply_colour_equation': __GEN_MANDATORY_COLS, '_apply_error_correction': __GEN_MANDATORY_COLS,
                        '_calibrate': __CAL_MANDATORY_COLS, 'calibrate': __CAL_MANDATORY_COLS,
                        '_convert': __CON_MANDATORY_COLS, 'convert': __CON_MANDATORY_COLS,
                        '_generate': __GEN_MANDATORY_COLS, 'generate': __GEN_MANDATORY_COLS,
                        'get_inverse_covariance_matrix': __INV_MANDATORY_COLS,
                        'get_inverse_square_root_covariance_matrix': __INV_MANDATORY_COLS}

# Preserve release identifiers when supplied without requiring them in the input.
OPTIONAL_INPUT_COLS = {
    '_apply_colour_equation': ['solution_id'], '_apply_error_correction': ['solution_id'],
    '_calibrate': ['solution_id'], 'calibrate': ['solution_id'],
    '_convert': ['solution_id'], 'convert': ['solution_id'],
    '_generate': ['solution_id'], 'generate': ['solution_id'],
    'get_inverse_covariance_matrix': ['solution_id'],
    'get_inverse_square_root_covariance_matrix': ['solution_id'],
}


def order_input_columns(columns):
    """Return shared fields first, followed by BP fields and then RP fields.

    Order within each group and duplicate names are preserved.
    """
    return ([column for column in columns if not column.startswith((f'{BANDS.bp}_', f'{BANDS.rp}_'))]
            + [column for column in columns if column.startswith(f'{BANDS.bp}_')]
            + [column for column in columns if column.startswith(f'{BANDS.rp}_')])


# A future reader may accept coefficients without requiring their uncertainties.
COEFFICIENT_ERRORS_REQUIRED = {
    '_calibrate': True, 'calibrate': True,
    '_convert': True, 'convert': True,
    '_generate': True, 'generate': True,
    'get_inverse_covariance_matrix': True,
    'get_inverse_square_root_covariance_matrix': True,
    '_apply_colour_equation': False, 'apply_colour_equation': False,
    '_apply_error_correction': False, 'apply_error_correction': False,
}


def requires_coefficient_errors(function_name) -> bool:
    """Return whether an operation requires coefficient error columns.

    Raises:
        ValueError: The operation has no registered requirement.
    """
    try:
        return COEFFICIENT_ERRORS_REQUIRED[function_name]
    except KeyError:
        raise ValueError(f'No coefficient error requirement is registered for {function_name!r}.') from None


TRUNCATION_COLS = ['bp_n_relevant_bases', 'rp_n_relevant_bases']

# Output columns
CAL_CORR_OUTPUT_COLS = ['correlation']
__CAL_OUTPUT_COLS = ['source_id', 'flux', 'flux_error']

CON_CORR_OUTPUT_COLS = ['correlation', 'standard_deviation']
__CON_OUTPUT_COLS = ['source_id', 'xp', 'flux', 'flux_error']

# Generator columns are not fixed but variable, depending on the systems involved; no correlation columns either.

# Whether all columns are present depends on the band(s) being requested
__INV_OUTPUT_COLS = ['source_id', 'bp_inverse_covariance', 'rp_inverse_covariance']
__INV_SQRT_OUTPUT_COLS = ['source_id', 'bp_inverse_square_root_covariance_matrix',
                          'rp_inverse_square_root_covariance_matrix']

DESIGN_INPUT_COLUMNS = ('bp_pwl_neighbour', 'rp_pwl_neighbour')

# Every top-level export must be classified here or in the description function.
# Tests compare these classifications with gaiaxpy.__all__ so new exports cannot
# silently miss an input-column description.
_READER_FUNCTIONS = {
    'calibrate': 'calibrate',
    'convert': 'convert',
    'generate': 'generate',
    'get_inverse_covariance_matrix': 'get_inverse_covariance_matrix',
    'get_inverse_square_root_covariance_matrix': 'get_inverse_square_root_covariance_matrix',
}
_CUSTOM_COLUMN_FUNCTIONS = {'plot_spectra', 'apply_error_correction'}
_NON_TABULAR_FUNCTIONS = {
    'get_chi2': 'Accepts a matrix and residual array.',
    'pwl_to_wl': 'Accepts pseudo-wavelength values and a band.',
    'wl_to_pwl': 'Accepts wavelength values and a band.',
    'pwl_range': 'Accepts a band and release.',
    'wl_range': 'Accepts a band and release.',
    'load_additional_systems': 'Accepts a filter directory.',
    'remove_additional_systems': 'Manages additional photometric systems.',
    'get_required_columns': 'Describes another function; does not consume tabular data.',
}
_NON_FUNCTION_EXPORTS = {'__version__', 'PhotometricSystem'}

_COLUMN_INFO = {
    'source_id': {'type': 'integer', 'description': 'Unique source identifier.'},
    'solution_id': {'type': 'integer',
                    'description': 'Solution identifier; checked for data release identification when supplied.'},
    'flux': {'type': 'array of floats', 'description': 'Spectrum flux values.', 'length': 'sampling length'},
    'flux_error': {'type': 'array of floats', 'description': 'Errors on the spectrum flux values.',
                   'length': 'sampling length'},
    'xp': {'type': 'string', 'description': f'Photometer: {BANDS.bp} or {BANDS.rp}.'},
    'DR3_GaiaVega_mag_G': {'type': 'float', 'description': 'DR3 Gaia Vega G magnitude.'},
    '{system}_flux_error_{band}': {'type': 'float', 'description': 'Flux error for the selected system and passband.'},
}
for __desc_xp in BANDS:
    __desc_band = __desc_xp.upper()
    __desc_parameter_column = f'{__desc_xp}_n_parameters'
    for __desc_suffix, __desc_type, __desc_description in (
            ('n_parameters', 'integer', f'Number of parameters for the {__desc_band} spectrum representation.'),
            ('standard_deviation', 'float', f'Standard deviation for the {__desc_band} spectrum representation.'),
            ('coefficients', 'array of floats',
             f'Basis function coefficients for the {__desc_band} spectrum representation.'),
            ('coefficient_errors', 'array of floats',
             f'Basis function coefficient errors for the {__desc_band} spectrum representation.'),
            ('coefficient_correlations', 'array of floats', f'Correlation matrix for {__desc_band} coefficients.'),
            ('coefficient_covariances', 'array of floats', f'Covariance matrix for {__desc_band} coefficients.'),
            ('n_relevant_bases', 'integer',
             f'Number of bases that are relevant for the representation of this mean {__desc_band} spectrum.'),
            ('pseudo_wavelength', 'array of floats', f'{__desc_band} sample pseudo-wavelengths.'),
            ('flux', 'array of floats', f'{__desc_band} sample flux values.'),
            ('flux_error', 'array of floats', f'Errors on the {__desc_band} sample flux values.')
    ):
        _COLUMN_INFO[f'{__desc_xp}_{__desc_suffix}'] = {'type': __desc_type, 'description': __desc_description}
    for __desc_suffix in ('coefficients', 'coefficient_errors'):
        _COLUMN_INFO[f'{__desc_xp}_{__desc_suffix}']['length'] = __desc_parameter_column
    _COLUMN_INFO[f'{__desc_xp}_coefficient_correlations']['length'] = (
        f'{__desc_parameter_column} * ({__desc_parameter_column} - 1) / 2'
    )
del __desc_xp, __desc_band, __desc_parameter_column, __desc_suffix, __desc_type, __desc_description


@dataclass(repr=False)
class ColumnRequirements:
    """Describe a public function's required and optional input columns.

    Attributes:
        function (str): Public function name.
        required (list[str]): Minimum input columns.
        alternatives (dict[str, list[str]]): Named alternative column groups.
        conditional (dict[str, list[str]]): Columns needed under each condition.
        optional (dict[str, list[str]]): Optional columns grouped by purpose.
        notes (list[str]): Input guidance and qualifications.
        column_info (dict[str, dict[str, str]]): Types, descriptions and array
            lengths where available.

    Printing the object shows the requirements first and omits empty sections.
    Type descriptions refer to cell values, not strict pandas dtypes.
    """

    function: str
    required: list[str] = field(default_factory=list)
    alternatives: dict[str, list[str]] = field(default_factory=dict)
    conditional: dict[str, list[str]] = field(default_factory=dict)
    optional: dict[str, list[str]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    column_info: dict[str, dict[str, str]] = field(default_factory=dict)

    def _format_columns(self, columns, indent=2):
        """Format column names with their available type and description text."""
        lines = []
        for column in columns:
            info = self.column_info.get(column)
            prefix = ' ' * indent
            if info:
                lines.append(fill(f'{column} ({info["type"]}): {info["description"]}', width=100,
                                  initial_indent=prefix, subsequent_indent=prefix + '  '))
            else:
                lines.append(prefix + column)
        return '\n'.join(lines)

    def _display_fields(self):
        """Copy the fields used by the readable display and documentation builder."""
        return list(self.required), dict(self.alternatives), list(self.notes)

    def __str__(self):
        """Format the requirements, conditional groups, optional columns and notes."""
        required, alternatives, notes = self._display_fields()
        sections = [self.function]
        if required:
            sections.append('Required input columns:\n' + self._format_columns(required))
        for groups, heading in (
                (alternatives, 'Also required (provide one complete group):'),
                (self.conditional, 'Conditional requirements:'),
                (self.optional, 'Optional columns:')
        ):
            if groups:
                entries = [heading]
                for condition, columns in groups.items():
                    entries.append(f'  {condition}:')
                    entries.append(self._format_columns(columns, indent=4))
                sections.append('\n'.join(entries))
        if notes:
            sections.append('Notes:\n' + '\n'.join(fill(note, width=88, initial_indent='  - ',
                                                        subsequent_indent='    ') for note in notes))
        return '\n\n'.join(sections)

    def __repr__(self):
        """Use the readable requirements display in interactive sessions."""
        return str(self)


def get_required_columns(function) -> ColumnRequirements:
    """Describe the local input columns of a public GaiaXPy function.

    Args:
        function (str or callable): Public function name, such as 'calibrate',
            or the GaiaXPy function itself.

    Returns:
        ColumnRequirements: Required columns, alternatives, conditional and
        optional groups, notes and column descriptions. Returned containers are
        independent copies. Names containing braces are patterns to replace
        with the relevant system and passband, rather than literal column names.

    Raises:
        TypeError: The argument is neither a name nor a GaiaXPy function.
        ValueError: The function is unknown or does not consume tabular data.

    Notes:
        Supports calibrate, convert, generate, get_inverse_covariance_matrix,
        get_inverse_square_root_covariance_matrix, plot_spectra and apply_error_correction.

        The descriptions cover local files and DataFrames, not ADQL query
        columns. For regular Archive-format coefficient tables, required columns
        include errors and correlations. No data, model files or Archive
        connection are needed to obtain these requirements.

    Examples:
        >>> from gaiaxpy import get_required_columns
        >>> get_required_columns('calibrate').required
    """
    if isinstance(function, str):
        name = function
    elif isfunction(function) and function.__module__.startswith('gaiaxpy.'):
        name = function.__name__
    else:
        raise TypeError('Expected a public GaiaXPy function name or function.')
    if name in _NON_TABULAR_FUNCTIONS:
        raise ValueError(f"'{name}' does not consume tabular spectra or photometry. "
                         f'{_NON_TABULAR_FUNCTIONS[name]}')
    supported = set(_READER_FUNCTIONS) | _CUSTOM_COLUMN_FUNCTIONS
    if name not in supported:
        raise ValueError(
            f"Unknown or unsupported function '{name}'. Supported functions: {', '.join(sorted(supported))}.")

    result = {'function': name, 'required': [], 'alternatives': {}, 'conditional': {}, 'optional': {}, 'notes': []}
    if name in _READER_FUNCTIONS:
        columns = MANDATORY_INPUT_COLS[_READER_FUNCTIONS[name]]
        result['required'] = list(columns)
        if 'solution_id' in OPTIONAL_INPUT_COLS[_READER_FUNCTIONS[name]]:
            result['optional']['release identification'] = ['solution_id']
            result['notes'].append(
                'solution_id is recommended for release identification. '
                'It identifies the release when recognised. If absent and no release is '
                'specified, DR3 is used by default.'
            )
        if requires_coefficient_errors(_READER_FUNCTIONS[name]):
            result['required'] = order_input_columns(result['required'] + CORR_INPUT_COLUMNS)
            result['notes'].extend([
                'Coefficients and errors each contain n_parameters values. Correlations contain '
                'n_parameters * (n_parameters - 1) / 2 values representing the upper triangle '
                'in column-major order, excluding the diagonal. The reader reconstructs a full '
                'symmetric correlation matrix with ones on the diagonal. If a full matrix is '
                'provided instead, it is preserved.',
                'If BP or RP is missing, keep its columns and use NaN for its n_parameters, coefficients, '
                'errors and correlations. Do not use n_parameters=0: release detection ignores null '
                'parameter counts but treats zero as invalid.',
                'Type labels describe values, not required pandas dtypes. An integer column containing '
                'NaN may have a float dtype.'
            ])
            if name in {
                'get_inverse_covariance_matrix',
                'get_inverse_square_root_covariance_matrix',
            }:
                result['notes'].append(
                    'Selecting a single output band does not remove the reader requirements '
                    'for the other band.'
                )
        if name in {'calibrate', 'convert', 'generate'}:
            result['conditional']['truncation=True'] = TRUNCATION_COLS
    elif name == 'plot_spectra':
        result['required'] = __CAL_OUTPUT_COLS
        result['conditional']['parameter multi=True with internally calibrated XP spectra'] = ['xp']
        result['notes'].extend(['Pass sampling separately. flux and flux_error arrays must match that sampling.',
                                "The DataFrame must retain attrs['data_type'], as set by calibrate or convert; "
                                'this is metadata, not a column. flux_error is accessed even with multi=True.'])
    elif name == 'apply_error_correction':
        result['required'] = ['{system}_flux_error_{band}', 'DR3_GaiaVega_mag_G']
        result['optional']['source identification'] = ['source_id']
        result['notes'].extend([
            'The source_id column is not required for this function to work, but retaining it is highly recommended '
            'as identifies the sources in the data.',
            'Use photometry returned by generate. DR3 correction tables are selected by default; '
            'the corresponding Gaia Vega reference photometry must be included in the input.',
            'Calling this function over the output of generate is equivalent to originally calling generate with '
            'error_correction=True.',
            'The braced system name is a pattern: replace system with the full release-prefixed system label '
            '(for example DR3_Jkc) and band with a passband name. Only available error columns with correction '
            'factors are corrected; other photometry is preserved.'
        ])
    else:
        raise NotImplementedError(f"Input-column description not implemented for '{name}'.")
    described_columns = set(result['required'])
    for group in ('alternatives', 'conditional', 'optional'):
        for columns in result[group].values():
            described_columns.update(columns)
    result['column_info'] = {column: _COLUMN_INFO[column] for column in sorted(described_columns)}
    return ColumnRequirements(**deepcopy(result))


def get_present_optional_columns(optional_columns, available_columns):
    """Return available optional columns once, preserving their candidate order.

    Args:
        optional_columns (iterable[str]): Optional names for the operation.
        available_columns (iterable[str]): Names present in the input table.

    Returns:
        list[str]: Available candidates. If solution_id is optional, its internal
        solutionId alias is also considered and may be returned alongside it.
    """
    candidates = list(optional_columns)

    if 'solution_id' in candidates:
        candidates.append('solutionId')

    return list(dict.fromkeys(column for column in candidates if column in available_columns))
