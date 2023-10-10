from gaiaxpy.input_reader.file_reader import FileReader


class LocalFileReader(FileReader):

    def __init__(self, file_parser_selector, file, additional_columns=None, selector=None, disable_info=False):
        self.file_content = file
        super().__init__(file_parser_selector, file, self.file_content, additional_columns, selector, disable_info)
