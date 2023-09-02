
class InvalidBandError(Exception):
    def __init__(self, band):
        self.message = f"String {band} is not a valid band. Band must be either 'bp' or 'rp'."
        super().__init__(self.message)


class SelectorNotImplementedError(Exception):
    def __init__(self, reader='This'):
        super().__init__(f'{reader} reader does not implement the selector functionality.')