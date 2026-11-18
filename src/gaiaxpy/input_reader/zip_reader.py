"""Read supported tables from a Gaia Archive ZIP download."""

from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

import pandas as pd

from gaiaxpy.core.generic_variables import VALID_EXTENSIONS
from gaiaxpy.input_reader.local_file_reader import LocalFileReader


class ZipReader:
    """Combine tables in a ZIP download into one input DataFrame.

    Supported members must all use the same file extension. Members
    are copied to temporary files and read through LocalFileReader;
    the temporary files are removed after reading.
    """

    def __init__(self, file_parser_selector, file, truncation, additional_columns=None, selector=None,
                 disable_info=False):
        """Store the ZIP filename and options passed to each LocalFileReader.

        Args:
            file_parser_selector (FileParserSelector): Parser factory for the
                operation that will use the data.
            file (str or pathlib.Path): ZIP filename.
            truncation (bool): Whether subsequent calculations use the recommended
                number of basis functions for each source and photometer. When True,
                this reader includes bp_n_relevant_bases and rp_n_relevant_bases.
                When False, calculations use all available basis functions.
            additional_columns (dict or None): Extra input-column mappings.
            selector (object or None): Selection passed to each file parser.
            disable_info (bool): Suppress routine reading messages.
        """
        self.fps = file_parser_selector
        self.file = file
        self.truncation = truncation
        self.additional_columns = additional_columns
        self.selector = selector
        self.disable_info = disable_info

    @staticmethod
    def _get_data_members(archive):
        """Validate that all ZIP members are files of one supported format."""
        members = []
        expected_extension = None

        for member in archive.infolist():
            if member.is_dir():
                raise ValueError(f'ZIP archive contains a directory entry: {member.filename!r}. '
                                 'Only files are expected.')

            extension = Path(member.filename).suffix.lstrip('.').lower()
            if extension not in VALID_EXTENSIONS:
                raise ValueError(f'ZIP member {member.filename!r} has an unsupported extension.')

            if expected_extension is None:
                expected_extension = extension
            elif extension != expected_extension:
                raise ValueError(f'ZIP member {member.filename!r} has extension {extension!r};'
                                 f'expected {expected_extension!r}.')

            members.append((member, extension))

        return members

    def read(self):
        """Read supported members and concatenate their rows in archive order.

        Returns:
            tuple[pandas.DataFrame, str]: Combined data with a fresh integer index,
            and the shared input extension without a dot.

        Raises:
            ValueError: The file is not a valid ZIP, contains no supported tables,
                or contains tables with different supported extensions.

        Notes:
            Errors reading an individual member are passed back to the caller.
            Member filenames are replaced with generated temporary filenames;
            archived directory paths are not recreated.
        """
        try:
            archive = ZipFile(self.file)
        except BadZipFile as error:
            raise ValueError(f'File {self.file} is not a valid ZIP archive.') from error

        with archive:
            members = self._get_data_members(archive)
            if not members:
                valid = ', '.join(VALID_EXTENSIONS)
                raise ValueError(f'ZIP archive {self.file} contains no supported input files. '
                                 f'Supported extensions are: {valid}.')

            extensions = {extension for _, extension in members}
            if len(extensions) != 1:
                raise ValueError(f'ZIP archive {self.file} contains multiple supported input formats: '
                                 f'{", ".join(sorted(extensions))}.')
            extension = extensions.pop()

            frames = []
            with TemporaryDirectory() as tmpdir:
                for index, (member, _) in enumerate(members):
                    extracted = Path(tmpdir) / f'{index}{Path(member.filename).suffix}'
                    with archive.open(member) as source, extracted.open('wb') as destination:
                        copyfileobj(source, destination)

                    reader = LocalFileReader(self.fps, extracted, self.truncation,
                                             additional_columns=self.additional_columns, selector=self.selector,
                                             disable_info=self.disable_info)
                    data, parsed_extension = reader.read()
                    if parsed_extension != extension:
                        raise ValueError(f'Unexpected extension {parsed_extension!r} while reading ZIP archive.')
                    frames.append(data)

        return pd.concat(frames, ignore_index=True), extension
