"""Configure the shared file reader for a local spectrum file."""

from gaiaxpy.input_reader.file_reader import FileReader


class LocalFileReader(FileReader):
    """Use FileReader with a local filename and the standard parser options."""

    def __init__(self, file_parser_selector, file, truncation, additional_columns=None, selector=None,
                 disable_info=False):
        """Forward the filename, column mappings and reading options to FileReader."""
        super().__init__(file_parser_selector, file, truncation, additional_columns, selector, disable_info)
