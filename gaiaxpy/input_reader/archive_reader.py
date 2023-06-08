class ArchiveReader(object):

    def __init__(self, function, user, password, disable_info=False):
        self.function = function
        self.user = user
        self.password = password
        self.disable_info = disable_info

    def _login(self, gaia):
        user = self.user
        password = self.password
        if user and password:
            gaia.login(user=user, password=password)
        else:
            pass
