"""Run an ADQL query and retrieve spectra for its source IDs."""

import re

from gaiaxpy.core.server import get_release_for_archive
from gaiaxpy.core.version import __version__
from .archive_reader import ArchiveReader
from .dataframe_reader import DataFrameReader
from .source_ids import validate_source_ids
from ..core.custom_errors import SelectorNotImplementedError
from ..core.generic_functions import get_function_name

not_supported_functions = ['apply_colour_equation']


class QueryReader(ArchiveReader):
    """Use an ADQL result to select spectra from the Gaia Archive.

    The query must return a recognised source ID column. Spectra are downloaded
    separately using those IDs.
    """

    def __init__(self, content, function, truncation, user=None, password=None, additional_columns=None, selector=None,
                 disable_info=False, release=None, retrieval_type=None, data_release=None,
                 result_key=None, archive_server=None, credentials_file=None):
        """Store the ADQL query and Archive reading options.

        Args:
            content (str): ADQL query returning a source-ID column.
            function (str or callable): Operation that will use the spectra.
            truncation (bool): Whether subsequent calculations use the recommended
                number of basis functions for each source and photometer. When True,
                this reader includes bp_n_relevant_bases and rp_n_relevant_bases.
                When False, calculations use all available basis functions.
            user (str or None): Cosmos username.
            password (str or None): Cosmos password.
            additional_columns (dict or None): Extra downloaded columns to retain.
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
        """
        if additional_columns is None:
            additional_columns = dict()
        if selector is not None:
            raise SelectorNotImplementedError('Query')
        self.content = content
        super(QueryReader, self).__init__(function, truncation, user, password, additional_columns=additional_columns,
                                          disable_info=disable_info, release=release,
                                          retrieval_type=retrieval_type, data_release=data_release,
                                          result_key=result_key, archive_server=archive_server,
                                          credentials_file=credentials_file)

    @staticmethod
    def get_srcids(_table):
        """Return the source ID column from an Astropy query-result table.

        Args:
            _table (astropy.table.Table): Query result to inspect.

        Returns:
            astropy.table.Column: The first column whose name matches source_id or
            src_id after ignoring case, hyphens, underscores and spaces. This
            returns the column values, not the name of the column.

        Raises:
            ValueError: No recognised source ID column is found, or its name is
                not a string.
        """
        try:
            stripped_pairs = ((re.sub(r'[-_ ]', '', c.lower()), c) for c in _table.columns.keys())
            sid_col = next(original for stripped, original in stripped_pairs if stripped in ['sourceid', 'srcid'])
        except StopIteration:
            raise ValueError('Source ID column not found in query result.')
        if not isinstance(sid_col, str):
            raise ValueError(
                f'Index of source ID column should be a string, but is {type(sid_col).__name__}: {sid_col}.')
        return _table[sid_col]

    @staticmethod
    def _add_marker(query, comment):
        """Prepend a single ADQL comment line without changing the original query.
        Intended for internal use only.

        An empty comment leaves the query unchanged. Newlines in the marker text
        are replaced with spaces.
        """
        if not comment:
            return query
        # Keep a custom marker on one comment line, including when it has newlines.
        marker = ' '.join(comment.splitlines())
        return f'--{marker}\n{query}'

    def read(self, _comment=f'This query was launched from within GaiaXPy {__version__}'):
        """Run the query, download its spectra and prepare the returned tables.

        Args:
            _comment (str): Query marker containing the GaiaXPy version by default.
                Pass an empty string to omit the marker.

        Returns:
            tuple[pandas.DataFrame, None]: Parsed spectrum data and no file extension.
            Row order follows the downloaded spectrum tables, not necessarily the
            ADQL result order.

        Raises:
            ValueError: The operation rejects ADQL, no source ID column is found,
                or no matching spectrum product is returned.

        Notes:
            Query, login, network and data-validation errors are passed back to the
            caller. Only source IDs from the query result are used for retrieval.
        """
        query = self.content
        query = self._add_marker(query, _comment)
        function_name = get_function_name(self.function)
        if function_name in not_supported_functions:
            raise ValueError(f'Function {function_name} does not accept ADQL queries.')
        # Connect to geapre
        gaia = self._get_archive_client()
        # ADQL query
        self.show_info_msg(message='Running Archive query...')
        job = self._archive_call(gaia.launch_job_async, query, dump_to_file=False)
        self.show_info_msg(message='Retrieving query results...')
        query_result = self._archive_call(job.get_results)
        data_release = self.data_release or get_release_for_archive(self.release)
        source_ids = self.get_srcids(query_result)
        # Preserve the existing handling of empty query results.
        if len(source_ids):
            source_ids = validate_source_ids(source_ids)
        self.show_info_msg(message=f'Downloading XP spectra (source IDs: {len(source_ids):,})...')
        result = self._archive_call(gaia.load_data, ids=source_ids, format='csv', data_structure=self.data_structure,
                                    retrieval_type=self.retrieval_type, data_release=data_release,
                                    avoid_datatype_check=True)
        self.show_info_msg(message='Reading downloaded spectra...')
        try:
            data = self._get_result_data(result)
        except (KeyError, IndexError):
            raise ValueError(f'No {self.retrieval_type} data found for the requested query.')
        parsed_data = DataFrameReader(data, function_name, self.truncation,
                                      additional_columns=self.additional_columns, disable_info=True).read()
        self.clear_info_msg()
        return parsed_data
