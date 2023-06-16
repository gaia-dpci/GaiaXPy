
class InvalidBandError(Exception):
    def __init__(self, band):
        self.message = f"String {band} is not a valid band. Band must be either 'bp' or 'rp'."
        super().__init__(self.message)
