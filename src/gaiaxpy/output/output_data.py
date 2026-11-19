"""Share output-format selection and saving status messages between writers."""
from ast import literal_eval
from os.path import dirname, abspath, join
from pathlib import Path

from numpy import set_printoptions

from gaiaxpy.core.generic_functions import _warning, standardise_extension
from gaiaxpy.core.input_validator import validate_overwrite
from gaiaxpy.file_parser.parse_generic import InvalidExtensionError
from .metadata import _csv_metadata_path

set_printoptions(legacy='1.21')


def _initialise_header():
    """Return the opening comment lines for a comma-delimited ECSV 1.0 table."""
    return ["# %ECSV 1.0", "# ---", "# delimiter: ','", "# datatype:"]


def _load_header_dict():
    """Read the bundled column descriptions and ECSV type declarations.

    Returns:
        dict: Column definitions parsed from ecsv_headers/headers_dict.txt.
        The file is read on each call.
    """
    current_path = dirname(abspath(__file__))
    header_dictionary_path = join(current_path, 'ecsv_headers', 'headers_dict.txt')
    with open(header_dictionary_path) as f:
        data = f.read()
    # Load header dictionary
    header_dict = literal_eval(data)
    return header_dict


class OutputData:
    """Hold a result table and dispatch saving to a format-specific writer.

    Subclasses implement the supported file formats. This base class selects the
    format and prints the saving status; it does not compute spectra or photometry.
    """

    _sampling_companion_formats = ()

    def __init__(self, data, positions):
        """Copy the result DataFrame and retain its sampling positions.

        Args:
            data (pandas.DataFrame): Result table, including its DataFrame attrs.
                The table is copied; arrays stored inside cells are not deep-copied.
            positions (array-like or None): Common sampling grid for sampled spectra,
                or None when the result does not have one. Retained without copying.
        """
        self.data = data.copy()
        self.positions = positions

    def save(self, save_file, output_path, output_file, output_format, extension, *, disable_info=False,
             overwrite="yes"):
        """Save the result using the selected format.

        Args:
            save_file (bool): Whether to write output. False validates overwrite
                and warns if it is 'ask', then returns without writing.
            output_path (str or pathlib.Path): Destination directory. Concrete
                writers create it, including missing parent directories.
            output_file (str): Filename stem, without the format extension.
            output_format (str or None): Avro, CSV, ECSV, FITS or XML/VOTable.
                Case and an initial dot are accepted. If omitted or empty, use
                extension to select the format. Avro support is intended for internal
                use only.
            extension (str): Underlying input format used as the default output format.
            disable_info (bool): Suppress routine saving messages.
            overwrite (str): 'yes' or 'y' replaces existing outputs (default: 'yes').
                'no' or 'n' raises FileExistsError on a collision. 'ask' prompts once
                for the main file and its companions. Values are case-insensitive.
                Declining or unavailable input skips saving. With save_file=False,
                'ask' prints a warning to stderr unless disable_info=True.

        Returns:
            None: Output is written to disk; this method does not return filenames.

        Raises:
            ValueError: overwrite is invalid, saving is enabled but output_file is None,
                or the format
                extension cannot be parsed.
            InvalidExtensionError: The selected format is unsupported.
            NotImplementedError: The subclass does not implement the selected writer.

        Notes:
            Output names are formed as <output_file>.<format>. Existing outputs are
            overwritten by default. A writer may also create sampling or metadata companions;
            the status message reports the main output filename. File and data
            conversion errors are passed back to the caller.
        """
        overwrite = validate_overwrite(overwrite)

        if not save_file:
            if overwrite == 'ask' and not disable_info:
                _warning("overwrite='ask' is ignored because save_file=False.")
            return

        if output_file is None:
            raise ValueError("output_file cannot be None.")

        output_format = standardise_extension(output_format or extension)

        save_methods = {
            'avro': self._save_avro,
            'csv': self._save_csv,
            'ecsv': self._save_ecsv,
            'fits': self._save_fits,
            'xml': self._save_xml
        }

        try:
            save_method = save_methods[output_format]
        except KeyError:
            raise InvalidExtensionError() from None

        destination = Path(output_path) / f'{output_file}.{output_format}'
        if overwrite not in ('yes', 'y') and not self._check_overwrite_policy(destination, output_format, overwrite):
            return
        if not disable_info:
            print('Saving file...', end='\r')
        save_method(output_path, output_file)
        if not disable_info:
            print(f"Done! Output saved to path: {destination}", end="\r")

    def _check_overwrite_policy(self, destination, output_format, overwrite):
        """Check the main output and its companions before calling the writer."""
        targets = [destination]
        if output_format == 'csv':
            # CSV writers also remove a stale metadata companion when metadata is absent.
            targets.append(_csv_metadata_path(destination))
        if output_format in self._sampling_companion_formats:
            targets.append(destination.with_name(f'{destination.stem}_sampling.{output_format}'))

        existing = [path for path in targets if path.exists() or path.is_symlink()]
        for path in existing:
            if path.is_dir():
                raise IsADirectoryError(path)
        if existing:
            names = ', '.join(str(path) for path in existing)
            if overwrite in ('no', 'n'):
                raise FileExistsError(f'Output already exists: {names}')
            try:
                answer = input(f'Replace existing output ({names})? [y/N] ')
            except (EOFError, OSError):
                return False
            if answer.strip().lower() not in ('y', 'yes'):
                return False

        return True

    def _save_avro(self, output_path, output_file):
        """Write Avro output in a subclass.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Raises:
            NotImplementedError: The base class has no Avro writer.
        """
        raise NotImplementedError()

    def _save_csv(self, output_path, output_file):
        """Write CSV output in a subclass.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Raises:
            NotImplementedError: The base class has no CSV writer.
        """
        raise NotImplementedError()

    def _save_ecsv(self, output_path, output_file):
        """Write ECSV output in a subclass.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Raises:
            NotImplementedError: The base class has no ECSV writer.
        """
        raise NotImplementedError()

    def _save_fits(self, output_path, output_file):
        """Write FITS output in a subclass.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Raises:
            NotImplementedError: The base class has no FITS writer.
        """
        raise NotImplementedError()

    def _save_xml(self, output_path, output_file):
        """Write XML/VOTable output in a subclass.

        Args:
            output_path (str or pathlib.Path): Destination directory.
            output_file (str): Filename stem without the format extension.

        Raises:
            NotImplementedError: The base class has no XML/VOTable writer.
        """
        raise NotImplementedError()
