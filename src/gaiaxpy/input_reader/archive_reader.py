from gaiaxpy.core.input_validator import check_column_overwrite
from gaiaxpy.input_reader.required_columns import CORR_INPUT_COLUMNS, MANDATORY_INPUT_COLS, TRUNCATION_COLS


class ArchiveReader(object):

    def __init__(self, function, truncation, user, password, additional_columns=None, disable_info=False):
        self.function = function
        self.truncation = truncation
        self.user = user
        self.password = password
        self.disable_info = disable_info
        self.info_msg = 'Running query...'
        # Columns
        self.additional_columns = dict() if additional_columns is None else additional_columns
        mandatory_columns = MANDATORY_INPUT_COLS.get(function.__name__, list())
        self.style_columns = CORR_INPUT_COLUMNS  # The Archive will always use correlations
        self.required_columns = list()
        if mandatory_columns:
            self.required_columns = mandatory_columns + self.style_columns
        if truncation:
            self.required_columns = self.required_columns + TRUNCATION_COLS
        self.requested_columns = self.required_columns
        if self.additional_columns:
            check_column_overwrite(additional_columns, self.required_columns)
            self.requested_columns = self.required_columns + [c for c in self.additional_columns.keys() if c not in
                                                              self.required_columns]

    def _login(self, gaia):
        user = self.user
        password = self.password
        if user and password:
            gaia.login(user=user, password=password)
        else:
            pass

    def show_info_msg(self, done=False):
        msg = self.info_msg
        if done:
            msg = msg + ' Done!'
        print(msg, end='\r')
