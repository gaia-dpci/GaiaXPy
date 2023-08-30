from gaiaxpy.core.generic_functions import format_additional_columns
from gaiaxpy.input_reader.required_columns import CORR_INPUT_COLUMNS, MANDATORY_INPUT_COLS


class ArchiveReader(object):

    def __init__(self, function, user, password, additional_columns=None, disable_info=False):
        additional_columns = [] if additional_columns is None else additional_columns
        self.function = function
        self.user = user
        self.password = password
        self.disable_info = disable_info
        self.info_msg = 'Running query...'
        mandatory_columns = MANDATORY_INPUT_COLS.get(function.__name__, list())
        self.required_columns = list()
        if mandatory_columns:
            self.required_columns = mandatory_columns + CORR_INPUT_COLUMNS  # The Archive will always use correlations
        self.additional_columns = format_additional_columns(additional_columns)
        if self.additional_columns:
            self.required_columns = self.required_columns + [c for c in additional_columns if c not in
                                                             self.required_columns]

    def _login(self, gaia):
        user = self.user
        password = self.password
        if user and password:
            gaia.login(user=user, password=password)
        else:
            pass
