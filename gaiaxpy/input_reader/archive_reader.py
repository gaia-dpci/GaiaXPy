class ArchiveReader(object):

    def __init__(self, function, user, password, disable_info=False):
        self.function = function
        self.user = user
        self.password = password
        self.disable_info = disable_info
        # Required columns doesn't really apply in Archive cases as the response will always contain the expected columns
        self.required_columns = list()

    def _login(self, gaia):
        user = self.user
        password = self.password
        if user and password:
            gaia.login(user=user, password=password)
        else:
            pass
