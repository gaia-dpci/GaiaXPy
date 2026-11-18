"""Share Archive client setup, login, result selection and status messages."""

import pandas as pd
from requests.exceptions import HTTPError

from gaiaxpy.core.generic_functions import get_function_name
from gaiaxpy.core.input_validator import check_column_overwrite
from gaiaxpy.core.server import get_retrieval_type_for_archive, get_server_for_archive
from gaiaxpy.input_reader.archive_output import archive_output, import_gaia_class
from gaiaxpy.input_reader.authentication import prepare_login_arguments, verify_login, login_error
from gaiaxpy.input_reader.login_response import capture_login_response
from gaiaxpy.input_reader.required_columns import (CORR_INPUT_COLUMNS, MANDATORY_INPUT_COLS, TRUNCATION_COLS,
                                                   requires_coefficient_errors, order_input_columns,
                                                   OPTIONAL_INPUT_COLS)


class ArchiveReader:
    """Provide common setup for ADQL and source ID Archive readers.

    Client creation and authentication are deferred until data are requested.
    Archive coefficient products use errors and correlations. Child readers
    retrieve the tables and pass them to DataFrameReader.
    """

    def __init__(self, function, truncation, user, password, additional_columns=None, disable_info=False, release=None,
                 retrieval_type=None, data_release=None, result_key=None, archive_server=None, credentials_file=None):
        """Store Archive options and determine the required input columns.

        Args:
            function (str or callable): Operation that will use the downloaded data.
            truncation (bool): Use the recommended number of basis functions for
            each source and photometer. When True, this reader includes
            bp_n_relevant_bases and rp_n_relevant_bases.
            When False, calculations use all available basis functions.
            user (str or None): Cosmos username.
            password (str or None): Cosmos password.
            additional_columns (dict or None): Columns to keep from the downloaded
            spectrum tables, mapping output names to lists of input column names.
            The columns must already exist in those tables. This option does not
            retrieve additional catalogue fields or preserve extra ADQL query
            columns. Columns used internally by GaiaXPy cannot be renamed or
            replaced through this mapping.
            disable_info (bool): Suppress routine status messages and Archive logs.
            release (str or None): Release used to select the default Archive server
                and data product.
            retrieval_type (str or None): Override the DataLink product type.
            data_release (str or None): Override the Archive data-release label.
            result_key (str or None): Fallback substring for DataLink result keys.
            archive_server (str or None): Override the Archive server URL.
            credentials_file (str or pathlib.Path or None): Two-line credentials file,
                used instead of user and password.

        Notes:
            Credentials are validated when the client is created, before contacting
            the server. An available interactive session may be used for login.
        """
        self.function = function
        self.truncation = truncation
        self.user = user
        self.password = password
        self.credentials_file = credentials_file
        self.disable_info = disable_info
        self.info_msg = 'Running query...'
        self._info_width = 0
        # Columns
        self.additional_columns = dict() if additional_columns is None else additional_columns
        mandatory_columns = MANDATORY_INPUT_COLS.get(get_function_name(function), list())
        self.style_columns = CORR_INPUT_COLUMNS  # The Archive will always use correlations
        self.required_columns = list(mandatory_columns)
        if requires_coefficient_errors(get_function_name(function)):
            self.required_columns += self.style_columns
        self.required_columns = order_input_columns(self.required_columns)
        if truncation:
            self.required_columns = self.required_columns + TRUNCATION_COLS
        self.requested_columns = self.required_columns
        if self.additional_columns:
            check_column_overwrite(additional_columns, self.required_columns
                                   + OPTIONAL_INPUT_COLS.get(get_function_name(function), []))
            self.requested_columns = self.required_columns + [c for c in self.additional_columns.keys() if c not in
                                                              self.required_columns]
        self.release = release
        self.retrieval_type = retrieval_type or get_retrieval_type_for_archive(release)
        self.data_release = data_release
        self.result_key = result_key
        self.archive_server = archive_server
        self.data_structure = 'DATAMODEL_GAIA'

    def _get_archive_client(self):
        # Resolve and validate credentials before Astroquery can contact a server.
        """Validate credentials, create the selected Archive client and log in."""
        login_arguments = prepare_login_arguments(self.user, self.password, self.credentials_file, self.release)
        server = self._get_archive_server()
        with archive_output(self.disable_info):
            GaiaClass = import_gaia_class()
            gaia = GaiaClass(gaia_tap_server=server, gaia_data_server=server,
                             show_server_messages=not self.disable_info)
        self._login(gaia, login_arguments=login_arguments)
        return gaia

    def _archive_call(self, operation, *args, **kwargs):
        """Run an Archive operation with the configured routine-log filtering."""
        with archive_output(self.disable_info):
            return operation(*args, **kwargs)

    def _login(self, gaia, *, login_arguments=None):
        """Log in when credentials are present and verify both Archive services.

        Authentication failures become ArchiveAuthenticationError. HTTP errors with
        statuses other than 401 or 403 retain their original exception.
        """
        if login_arguments is None:
            login_arguments = prepare_login_arguments(self.user, self.password, self.credentials_file, self.release)
        if not login_arguments:
            return
        if not self.disable_info:
            print('Contacting the Gaia Archive...')
        try:
            with capture_login_response(gaia) as failure:
                self._archive_call(gaia.login, **login_arguments)
            if failure.error is not None:
                raise failure.error
        except HTTPError as error:
            status = getattr(error.response, 'status_code', None)
            if status is not None and status not in (401, 403):
                raise  # Preserve server/service errors instead of blaming credentials.
            raise login_error(self.release, status) from None
        verify_login(gaia, self.release)

    def _get_result_keys(self, result):
        """Find DataLink keys starting with the retrieval type, ignoring case.

        If none match, use result_key as a substring fallback when it is supplied.
        Result order is preserved.
        """
        retrieval_type = self.retrieval_type.lower()
        matches = [key for key in result if key.lower().startswith(retrieval_type)]
        if not matches and self.result_key:
            matches = [key for key in result if self.result_key.lower() in key.lower()]
        return matches

    def _get_result_key(self, result):
        """Return the first matching DataLink key, or None if no key matches."""
        matches = self._get_result_keys(result)
        return matches[0] if matches else None

    def _get_result_data(self, result):
        """Combine the first table under each matching DataLink key.

        Args:
            result (dict): DataLink result mapping, with a table sequence per key.

        Returns:
            pandas.DataFrame: Combined tables with a fresh integer index.

        Raises:
            KeyError: No DataLink key matches the selected product.
            IndexError: A matching result contains no table.
        """
        keys = self._get_result_keys(result)
        if not keys:
            raise KeyError
        frames = [result[key][0].to_pandas() for key in keys]
        return pd.concat(frames, ignore_index=True)

    def _get_archive_server(self):
        """Return the server override or the default server for the release."""
        return self.archive_server or get_server_for_archive(self.release)

    def show_info_msg(self, done=False, message=None):
        """Update the current status line unless routine messages are disabled.

        Args:
            done (bool): Append a completion marker.
            message (str or None): Override the reader's default status message.
        """
        if self.disable_info:
            return
        msg = message if message is not None else self.info_msg
        if done:
            msg = msg + ' Done!'
        width = max(self._info_width, len(msg))
        print(f'\r{msg.ljust(width)}', end='\r', flush=True)
        self._info_width = width

    def clear_info_msg(self):
        """Erase the current status line unless routine messages are disabled."""
        if not self.disable_info and self._info_width:
            print('\r' + ' ' * self._info_width, end='\r', flush=True)
            self._info_width = 0
