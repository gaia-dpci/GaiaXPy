from gaiaxpy.input_reader.file_reader import FileReader


class LocalFileReader(FileReader):

    def __init__(self, file_parser_selector, file, truncation, additional_columns=None, selector=None,
                 disable_info=False):
        super().__init__(file_parser_selector, file, truncation, additional_columns, selector, disable_info)
