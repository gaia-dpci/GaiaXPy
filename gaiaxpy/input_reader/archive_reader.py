from astroquery.gaia import GaiaClass

class ArchiveReader(object):

    def __init__(self, function, user, password):
        self.function = function
        self.user = user
        self.password = password

    def _login(self, gaia):
        user = self.user
        password = self.password
        if user and password:
            gaia.login(user=user, password=password)
        else:
            gaia.login()
