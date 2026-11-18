"""Retrieve Archive spectra for a source ID selection."""

from gaiaxpy.core.server import get_release_for_archive
from .archive_reader import ArchiveReader
from .dataframe_reader import DataFrameReader
from .source_ids import validate_source_ids
from ..core.custom_errors import SelectorNotImplementedError
from ..core.generic_functions import get_function_name

not_supported_functions = ['apply_colour_equation', 'apply_error_correction']


def extremes_are_enclosing(first_row, column):
    """Check whether a non-empty string cell uses matching square or round brackets."""
    if first_row[column][0] == '[' and first_row[column][-1] == ']':
        return True
    elif first_row[column][0] == '(' and first_row[column][-1] == ')':
        return True
    else:
        return False


class IterableReader(ArchiveReader):
    """Download source ID selections and prepare the returned spectrum tables.

    Source IDs are validated before retrieval. The Archive result is then processed
    by DataFrameReader using the requirements of the selected operation.
    """

    def __init__(self, content, function, truncation, user, password, additional_columns=None, selector=None,
                 disable_info=False, release=None, retrieval_type=None, data_release=None,
                 result_key=None, archive_server=None, credentials_file=None):
        """Store Archive options and validate the source ID selection.

        Args:
            content (iterable of int or str): Non-empty source ID selection,
                including a list or tuple. Python/NumPy integers and decimal
                integer strings may be mixed. Values are normalised to integers
                before retrieval; booleans, floats and missing values are rejected.
            function (str or callable): Operation that will use the downloaded data.
            truncation (bool): Whether subsequent calculations use the recommended
                number of basis functions for each source and photometer. When True,
                this reader includes bp_n_relevant_bases and rp_n_relevant_bases.
                When False, calculations use all available basis functions.
            user (str or None): Cosmos username.
            password (str or None): Cosmos password.
            additional_columns (dict or None): Extra column mappings.
            selector (None): Reserved argument; selectors are not supported here.
            disable_info (bool): Suppress routine reading messages.
            release (str or None): Gaia release used for Archive access.
            retrieval_type (str or None): Override the Archive product type.
            data_release (str or None): Override the Archive data-release label.
            result_key (str or None): Fallback substring for DataLink result keys.
            archive_server (str or None): Override the Archive server URL.
            credentials_file (str or pathlib.Path or None): Two-line credentials file.

        Raises:
            SelectorNotImplementedError: selector is not None.
            TypeError: Source IDs are not valid integer values.
            ValueError: The source ID selection is empty.
        """
        if selector is not None:
            raise SelectorNotImplementedError('List')
        if additional_columns is None:
            additional_columns = dict()
        super(IterableReader, self).__init__(function, truncation, user, password,
                                             additional_columns=additional_columns,
                                             disable_info=disable_info, release=release,
                                             retrieval_type=retrieval_type, data_release=data_release,
                                             result_key=result_key, archive_server=archive_server,
                                             credentials_file=credentials_file)
        self.content = validate_source_ids(content)
        self.disable_info = disable_info
        self.release = release

    def read(self):
        """Retrieve matching spectra and prepare them using DataFrameReader.

        Returns:
            tuple[pandas.DataFrame, None]: Parsed Archive data and no file extension.
            Row order follows the returned Archive tables.

        Raises:
            ValueError: The operation does not accept source ID input, or no
                matching spectrum product is returned.

        Notes:
            Authentication, network and input-column errors are passed back to
            the caller. This method does not apply InputReader's coefficient correction
            as it is always expected to be called from within InputReader which does apply
            the correction if requested.
        """
        function_name = get_function_name(self.function)
        sources = self.content
        if function_name in not_supported_functions:
            raise ValueError(f'Function {function_name} does not support receiving a list as input.')
        # Connect to gea
        gaia = self._get_archive_client()
        self.show_info_msg(message=f'Downloading XP spectra (source IDs: {len(sources):,})...')
        data_release = self.data_release or get_release_for_archive(self.release)
        result = self._archive_call(gaia.load_data, ids=sources, format='csv', data_release=data_release,
                                    data_structure=self.data_structure, retrieval_type=self.retrieval_type,
                                    avoid_datatype_check=True)
        self.show_info_msg(message='Reading downloaded spectra...')
        try:
            data = self._get_result_data(result)
        except (KeyError, IndexError):
            raise ValueError(f'No {self.retrieval_type} data found for the given sources.')
        parsed_data = DataFrameReader(data, function_name, self.truncation,
                                      additional_columns=self.additional_columns, disable_info=True).read()
        self.clear_info_msg()
        return parsed_data
