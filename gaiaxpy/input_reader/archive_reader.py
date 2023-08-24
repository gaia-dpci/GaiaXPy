from gaiaxpy.input_reader.required_columns import CORR_INPUT_COLUMNS, MANDATORY_INPUT_COLS


class ArchiveReader(object):

    def __init__(self, function, user, password, disable_info=False):
        self.function = function
        self.user = user
        self.password = password
        self.disable_info = disable_info
        mandatory_columns = MANDATORY_INPUT_COLS.get(function.__name__, list())
        required_columns = list()
        if mandatory_columns:
            required_columns = mandatory_columns + CORR_INPUT_COLUMNS  # The Archive will always use correlations
        self.required_columns = required_columns

    def _login(self, gaia):
        user = self.user
        password = self.password
        if user and password:
            gaia.login(user=user, password=password)
        else:
            pass
