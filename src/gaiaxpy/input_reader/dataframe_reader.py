"""Select input columns and prepare array and matrix fields in DataFrames."""

import numpy as np
import pandas as pd

from .dataframe_numpy_array_reader import DataFrameNumPyArrayReader
from .dataframe_string_array_reader import DataFrameStringArrayReader
from .normalisation import get_array_columns, normalise_input_data
from .required_columns import (MANDATORY_INPUT_COLS, COV_INPUT_COLUMNS, CORR_INPUT_COLUMNS, TRUNCATION_COLS,
                               requires_coefficient_errors, OPTIONAL_INPUT_COLS, order_input_columns,
                               get_present_optional_columns)
from ..core.custom_errors import SelectorNotImplementedError
from ..core.generic_functions import array_to_symmetric_matrix, rename_with_required, get_function_name
from ..core.input_validator import check_column_overwrite
from ..core.satellite import BANDS
from ..file_parser.cast import _cast
from ..spectrum.utils import get_covariance_matrix

covariance_columns = ['bp_covariance_matrix', 'rp_covariance_matrix']
matrix_columns = [('bp_n_parameters', 'bp_coefficient_correlations'),
                  ('rp_n_parameters', 'rp_coefficient_correlations')]


def extremes_are_enclosing(row, column):
    """Check whether a non-empty string cell starts and ends with matching brackets."""
    return (row[column][0] == '(' and row[column][-1] == ')') or (row[column][0] == '[' and row[column][-1] == ']')


def needs_matrix_conversion(array_columns):
    """Return the correlation-column names present in array_columns."""
    columns_to_matrix = (column for value, column in matrix_columns)
    return set(columns_to_matrix).intersection(set(array_columns))


class DataFrameReader:
    """Prepare a DataFrame for a GaiaXPy operation.

    The reader keeps a copy with a fresh integer index. It normalises recognised
    array fields, reconstructs coefficient correlation matrices where needed and
    selects the requested columns.
    """

    def __init__(self, content, function, truncation, additional_columns=None, selector=None, disable_info=False):
        """Copy the DataFrame and determine the columns to retain.

        Args:
            content (pandas.DataFrame): Input table. Cells may contain NumPy arrays
                or supported text representations of arrays.
            function (str or callable): Operation that will use the data.
            truncation (bool): Whether subsequent calculations use the recommended
                number of basis functions for each source and photometer. When True,
                this reader includes bp_n_relevant_bases and rp_n_relevant_bases
                for that calculation. When False, calculations use all available
                basis functions.
            additional_columns (dict or None): Extra columns to keep from the input
            DataFrame. Maps each desired output name to a one-element list containing
            the input column name, for example {'g_mag': ['phot_g_mean_mag']} will
            cause the original 'phot_g_mean_mag' column to be present in the output
            as 'g_mag'. Columns used internally by GaiaXPy cannot be renamed or
            replaced through this mapping.
            selector (None): Reserved argument; selectors are not supported here.
            disable_info (bool): Suppress routine reading messages.

        Raises:
            ValueError: content is not a DataFrame, or a complete set of required
                uncertainty columns is unavailable.
            SelectorNotImplementedError: selector is not None.
        """
        if not isinstance(content, pd.DataFrame):
            raise ValueError('Input to read must be a DataFrame.')
        if selector is not None:
            raise SelectorNotImplementedError('DataFrame')
        self.additional_columns = dict() if additional_columns is None else additional_columns
        self.content = content.copy().reset_index(drop=True)
        self.function_name = get_function_name(function)
        self.disable_info = disable_info
        self.info_msg = 'Reading input DataFrame...'
        self.columns = self.content.columns
        mandatory_columns = MANDATORY_INPUT_COLS.get(self.function_name, list())
        self.required_columns = DataFrameReader.get_required_columns(
            content, mandatory_columns, requires_coefficient_errors(self.function_name))
        if truncation:
            self.required_columns = self.required_columns + TRUNCATION_COLS
        optional_columns = OPTIONAL_INPUT_COLS.get(self.function_name, [])
        present_optional = get_present_optional_columns(optional_columns, content.columns)
        self.requested_columns = self.required_columns + present_optional
        if self.additional_columns:
            check_column_overwrite(additional_columns, self.requested_columns)
            self.requested_columns += [c for c in self.additional_columns.keys() if c not in
                                       self.requested_columns]

    @staticmethod
    def get_required_columns(content, mandatory_columns, requires_errors):
        """Choose the columns needed for the operation.

        Args:
            content (pandas.DataFrame): Input whose column names are inspected.
            mandatory_columns (list[str]): Base requirements for the operation.
            requires_errors (bool): Whether to include coefficient errors columns.

        Returns:
            list[str]: Ordered column names. A complete correlation/error set takes
            precedence over covariance columns when both are available.

        Raises:
            ValueError: Errors are required but neither complete set exists.
        """
        style_columns = list()
        if requires_errors:
            missing_corr = [col for col in CORR_INPUT_COLUMNS if col not in content.columns]
            has_all_cov = all(col in content.columns for col in COV_INPUT_COLUMNS)

            if not missing_corr:
                style_columns = CORR_INPUT_COLUMNS
            elif has_all_cov:
                style_columns = COV_INPUT_COLUMNS
            else:
                missing_cov = [col for col in COV_INPUT_COLUMNS if col not in content.columns]
                raise ValueError(
                    f"Input DataFrame must contain either all required covariance columns or all correlation "
                    f"columns. Missing covariance columns: {', '.join(missing_cov)}. Missing correlation "
                    f"columns: {', '.join(missing_corr)}.")
        return order_input_columns(mandatory_columns + style_columns)

    def __get_parseable_columns(self):
        """Inspect the first two rows for bracketed strings and NumPy array cells.

        Returns:
            tuple[list[str], list[str]]: Candidate string-array and NumPy-array
            column names. This fallback is used when no recognised array fields
            are present for the operation.
        """
        str_columns, np_columns = [], []
        content = self.content
        rows = content.iloc[0:2]
        rows_dict = rows.to_dict('records')
        for row in rows_dict:
            for column in content.columns:
                if isinstance(row[column], str) and extremes_are_enclosing(row, column):
                    str_columns.append(column)
                if isinstance(row[column], np.ndarray):
                    np_columns.append(column)
        return list(set(str_columns)), list(set(np_columns))

    def read(self):
        """Convert array fields, prepare matrices and select the requested columns.

        Returns:
            tuple[pandas.DataFrame, None]: Prepared data and no file extension.
            The caller's DataFrame is not modified.

        Notes:
            Known scalar columns are cast to the shared input types. Correlation
            inputs also produce BP and RP covariance-matrix columns. Extra column
            mappings are applied before the final column selection.
        """
        if not self.disable_info:
            self.show_info_msg()
        content = self.content
        schema_array_columns = get_array_columns(self.function_name).intersection(content.columns)
        if schema_array_columns:
            data = normalise_input_data(content, self.function_name)
            array_columns = list(schema_array_columns)
        else:
            str_array_columns, np_array_columns = self.__get_parseable_columns()
            if str_array_columns:
                data = DataFrameStringArrayReader(content, str_array_columns).read()
                array_columns = str_array_columns
            elif np_array_columns:
                data = DataFrameNumPyArrayReader(content, np_array_columns).read()
                array_columns = np_array_columns
            else:
                data = content
                array_columns = []
        if needs_matrix_conversion(array_columns):
            for size_column, values_column in matrix_columns:
                data[values_column] = [array_to_symmetric_matrix(array, size) for array, size in zip(
                    data[values_column], data[size_column])]
            if matrix_columns:
                for band in BANDS:
                    data[f'{band}_covariance_matrix'] = data.apply(get_covariance_matrix, axis=1, args=(band,))
                self.requested_columns = self.requested_columns + covariance_columns
        if not self.disable_info:
            self.show_info_msg(done=True)
        data = _cast(data)
        if self.additional_columns:
            data = rename_with_required(data, self.additional_columns)
        data = data[self.requested_columns] if self.requested_columns else data
        # No extension returned for DataFrames
        return data, None

    def show_info_msg(self, done=False):
        """Print the DataFrame reading status, optionally marked as complete."""
        msg = self.info_msg
        if done:
            msg = msg + ' Done!'
        print(msg, end='\r')
