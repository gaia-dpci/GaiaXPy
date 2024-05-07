import re

from astroquery.gaia import GaiaClass

from gaiaxpy.core.server import data_release, gaia_server
from .archive_reader import ArchiveReader
from .dataframe_reader import DataFrameReader
from ..core.custom_errors import SelectorNotImplementedError

not_supported_functions = ['apply_colour_equation']


class QueryReader(ArchiveReader):

    def __init__(self, content, function, truncation, user=None, password=None, additional_columns=None, selector=None,
                 disable_info=False):
        if additional_columns is None:
            additional_columns = dict()
        if selector is not None:
            raise SelectorNotImplementedError('Query')
        self.content = content
        super(QueryReader, self).__init__(function, truncation, user, password, additional_columns=additional_columns,
                                          disable_info=disable_info)

    @staticmethod
    def get_srcids(_table):
        """
        Get the name of the source ID column from an Astropy Table.

        Args:
            _table (Table): A table containing columns.

        Returns:
            str: The name of the source ID column.

        Raises:
            ValueError: If the source ID column is not found in the DataFrame.
            ValueError: If the index of the source ID column is not a string.
        """
        try:
            stripped_pairs = ((re.sub(r'[-_ ]', '', c.lower()), c) for c in _table.columns.keys())
            sid_col = next(original for stripped, original in stripped_pairs if stripped in ['sourceid', 'srcid'])
        except StopIteration:
            raise ValueError('Source ID column not found in query result.')
        if not isinstance(sid_col, str):
            raise ValueError(f'Index of source ID column should be a string, but is {type(sid_col).__name__}: {sid_col}.')
        return _table[sid_col]

    def read(self, _data_release=data_release):
        query = self.content
        function_name = self.function.__name__
        if function_name in not_supported_functions:
            raise ValueError(f'Function {function_name} does not accept ADQL queries.')
        # Connect to geapre
        gaia = GaiaClass(gaia_tap_server=gaia_server, gaia_data_server=gaia_server)
        self._login(gaia)
        # ADQL query
        if not self.disable_info:
            print(self.info_msg, end='\r')
        job = gaia.launch_job_async(query, dump_to_file=False)
        query_result = job.get_results()
        result = gaia.load_data(ids=self.get_srcids(query_result), format='csv', data_release=_data_release,
                                data_structure='raw', retrieval_type='XP_CONTINUOUS', avoid_datatype_check=True)
        try:
            continuous_key = [key for key in result.keys() if 'continuous' in key.lower()][0]
            data = result[continuous_key][0].to_pandas()
        except KeyError:
            raise ValueError('No continuous raw data found for the requested query.')
        if not self.disable_info:
            print(self.info_msg + ' Done!', end='\r')
        return DataFrameReader(data, function_name, self.truncation, additional_columns=self.additional_columns,
                               disable_info=True).read()
