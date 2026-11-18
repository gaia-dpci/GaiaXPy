"""Choose an input reader, check the data release and apply input corrections."""

from os.path import isfile
from pathlib import Path

import pandas as pd

from .dataframe_reader import DataFrameReader
from .file_reader import FileParserSelector
from .hdfs_reader import HDFSReader
from .list_reader import IterableReader
from .local_file_reader import LocalFileReader
from .normalisation import normalise_input_data
from .query_reader import QueryReader
from .zip_reader import ZipReader
from ..core.generic_functions import get_function_name
from ..core.generic_variables import RELEASES
from ..core.release_resolution import is_release_redundant, get_release_from_data

default_extension = 'csv'


class InputReader:
    """Input reading class for a GaiaXPy operation.

    Reading is deferred until :meth:`read` is called. Column requirements and file
    parsers depend on the requested operation. Archive inputs use DR3 by default;
    local data are checked against any release supplied by the caller.
    """

    def __init__(self, content, function, truncation, additional_columns=None, selector=None, disable_info=False,
                 user=None, password=None, release=None, retrieval_type=None, data_release=None, result_key=None,
                 archive_server=None, credentials_file=None):
        """Store the input and options used by :meth:`read`.

        Args:
            content (str, pathlib.Path, pandas.DataFrame, pandas.Series, list or tuple): Local
                filename, DataFrame, single spectrum row as a Series, ADQL query
                beginning with SELECT, or source IDs.
                Local ZIP downloads are also accepted. Supported input types depend
                on the operation.
            function (str or callable): GaiaXPy operation that will use the data.
            truncation (bool): Whether subsequent calculations use the recommended
                number of basis functions for each source and photometer. When True,
                this reader includes bp_n_relevant_bases and rp_n_relevant_bases.
                When False, calculations use all available basis functions.
            additional_columns (dict or None): Extra columns to retain, keyed by
                output name. File mappings specify the input field or nested path.
            selector (object or None): Selection passed to the file parser. DataFrame
                and Archive readers reject a non-None selector.
            disable_info (bool): Suppress routine reading messages. Authentication
                prompts, warnings and errors may still appear.
            user (str or None): Cosmos username for Archive access.
            password (str or None): Cosmos password. Requires a username.
            release (str or None): Gaia release. Defaults to 'dr3' for
                ADQL queries and source ID selections, as well as inputs
                whose release cannot be identified.
            retrieval_type (str or None): Override the Archive data product.
            data_release (str or None): Override the Archive data-release label.
            result_key (str or None): Fallback text for locating DataLink results
                when no key starts with the retrieval type.
            archive_server (str or None): Override the Archive server URL.
            credentials_file (str or pathlib.Path or None): UTF-8 file containing
                the Cosmos username and password on separate lines. Cannot be
                combined with user or password.

        Raises:
            ValueError: additional_columns is not a dictionary.

        Notes:
            File access, Archive login and data validation happen during read().
            ``applied_correction_files`` records files used by the input correction.
        """
        if additional_columns is None:
            additional_columns = dict()
        self.additional_columns = additional_columns
        if not isinstance(self.additional_columns, dict):
            raise ValueError(f'Additional columns is {type(self.additional_columns).__name__}.')
        self.selector = selector if selector is None else selector
        self.content = content
        self.function = function
        self.truncation = truncation
        self.disable_info = disable_info
        self.user = user
        self.password = password
        self.credentials_file = credentials_file
        self.release = release
        self.retrieval_type = retrieval_type
        self.data_release = data_release
        self.result_key = result_key
        self.archive_server = archive_server
        self.applied_correction_files = []

    def read(self):
        """Read the input, normalise array fields and check the data release.

        Returns:
            tuple[pandas.DataFrame, str, str or None]: Parsed data, underlying input
            extension without a dot, and resolved release. DataFrame and Archive
            inputs use 'csv' as the default output extension. The release may be
            None for operations that do not need it.

        Raises:
            FileNotFoundError: A filename does not identify an existing file.
            ValueError: The input type is unsupported, the detected and requested releases disagree.

        Notes:
            The selected reader may also raise errors for unsupported formats,
            missing columns, invalid data or Archive access. The resolved release
            is stored on this reader before the requested correction is applied.
        """
        content = self.content
        function = self.function
        truncation = self.truncation
        disable_info = self.disable_info
        additional_columns = self.additional_columns
        selector = self.selector
        release = self.release
        function_name = get_function_name(function)
        # Input data directly provided by the user
        if isinstance(content, pd.Series):
            content = pd.DataFrame([content.tolist()], columns=content.index)
        if isinstance(content, pd.DataFrame):
            reader = DataFrameReader(content, function, truncation, additional_columns=additional_columns,
                                     selector=selector, disable_info=disable_info)
        elif isinstance(content, Path) or isinstance(content, str):
            if isfile(content):
                parser = FileParserSelector(function)
                if Path(content).suffix.lower() == '.zip':
                    reader = ZipReader(parser, content, truncation, additional_columns=additional_columns,
                                       selector=selector, disable_info=disable_info)
                else:
                    reader = LocalFileReader(parser, content, truncation, additional_columns=additional_columns,
                                             selector=selector, disable_info=disable_info)
            elif isinstance(content, str) and content.lstrip().lower().startswith('select'):
                release = InputReader._require_archive_release(release)
                reader = QueryReader(content, function, truncation, user=self.user, password=self.password,
                                     credentials_file=self.credentials_file,
                                     additional_columns=additional_columns, selector=selector,
                                     disable_info=disable_info, release=release, retrieval_type=self.retrieval_type,
                                     data_release=self.data_release, result_key=self.result_key,
                                     archive_server=self.archive_server)
            else:
                raise FileNotFoundError(f'File {content} does not exist')
        # Actual input data got from the Archive
        elif isinstance(content, (list, tuple)):
            release = InputReader._require_archive_release(release)
            reader = IterableReader(content, function, truncation, user=self.user, password=self.password,
                                    credentials_file=self.credentials_file,
                                    additional_columns=additional_columns, selector=selector, disable_info=disable_info,
                                    release=release, retrieval_type=self.retrieval_type,
                                    data_release=self.data_release, result_key=self.result_key,
                                    archive_server=self.archive_server)
        elif isinstance(content, str) and content.lower().startswith('hdfs://'):
            parser = FileParserSelector(function)
            reader = HDFSReader(parser, content, truncation, additional_columns=additional_columns, selector=selector,
                                disable_info=disable_info)
        else:
            raise ValueError(f'The input provided does not match any of the expected input types. The input type is'
                             f' {type(content).__name__}.')
        parsed_data, extension = reader.read()
        parsed_data = normalise_input_data(parsed_data, function)
        self.release = self.check_releases_match(parsed_data)
        extension = default_extension if extension is None else extension
        return parsed_data, extension, self.release

    @staticmethod
    def _require_archive_release(release) -> str:
        """Default Archive queries and source ID selections to DR3.

        An explicitly supplied release is passed through without validation.
        """
        if release is None:
            return RELEASES.dr3
        return release

    def check_releases_match(self, parsed_data):
        """Resolve the release and compare it with the caller's selection.

        Args:
            parsed_data (pandas.DataFrame): Input used by the release-detection rules
                for the selected operation.

        Returns:
            str or None: Detected release, or the supplied release when detection
            cannot determine one. None is allowed when the operation does not
            require a release.

        Raises:
            ValueError: The detected release differs from the supplied release.
        """
        detected_release = get_release_from_data(parsed_data, self.function)
        if detected_release is None:
            if is_release_redundant(self.function):
                return self.release
            if self.release:
                return self.release
            return RELEASES.dr3
        if not self.release:
            return detected_release
        if detected_release != self.release:
            raise ValueError(f"The selected release is '{self.release}', but the input data "
                             f"were identified as '{detected_release}'.")
        return detected_release
