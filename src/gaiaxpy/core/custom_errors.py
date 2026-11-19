class ExtensionNotImplementedError(Exception):
    def __init__(self, extension):
        super().__init__(f"This functionality is not implemented for the file extension '{extension}'")


class InvalidBandError(Exception):
    def __init__(self, band):
        self.message = f"String {band} is not a valid band. Band must be either 'bp' or 'rp'."
        super().__init__(self.message)


class NoBandsAvailableError(Exception):
    def __init__(self):
        super().__init__('No bands present in the input data. At least one band must be available.')


class InvalidReleaseError(Exception):
    def __init__(self, release):
        self.message = (f"String '{release}' is not a valid release. Release must be 'dr3'. Please "
                        "provide a valid release via the 'release' parameter.")
        super().__init__(self.message)


class ArchiveAuthenticationError(Exception):
    def __init__(self, release, reason=None, *, include_guidance=True):
        explanation = f'Login to the Gaia {release.upper()} Archive is required for this request.'
        if not include_guidance:
            self.message = reason or explanation
            super().__init__(self.message)
            return
        self.message = (f'{reason + " " if reason else ""}{explanation} '
                        "Use an interactive terminal/notebook to enter your password at a hidden prompt, "
                        "or pass credentials_file='path/to/credentials.txt' (username and password on separate lines). "
                        'Supplying both username and password is also supported for non-interactive use.')
        super().__init__(self.message)


class SelectorNotImplementedError(Exception):
    def __init__(self, reader='This'):
        super().__init__(f'{reader} reader does not implement the selector functionality.')
