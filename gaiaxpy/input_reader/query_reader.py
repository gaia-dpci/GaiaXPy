from astroquery.gaia import GaiaClass

from gaiaxpy.core.server import data_release, gaia_server
from .archive_reader import ArchiveReader
from .dataframe_reader import DataFrameReader
from ..core.custom_errors import SelectorNotImplementedError

not_supported_functions = ['apply_colour_equation', 'simulate_continuous', 'simulate_sampled']


class QueryReader(ArchiveReader):

    def __init__(self, content, function, user=None, password=None, additional_columns=None, selector=None,
                 disable_info=False):
        if additional_columns is None:
            additional_columns = dict()
        if selector is not None:
            raise SelectorNotImplementedError('Query')
        self.content = content
        super(QueryReader, self).__init__(function, user, password, additional_columns=additional_columns,
                                          disable_info=disable_info)

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
        ids = job.get_results()
        result = gaia.load_data(ids=ids['source_id'], format='csv', data_release=_data_release,
                                data_structure='raw', retrieval_type='XP_CONTINUOUS', avoid_datatype_check=True)
        try:
            continuous_key = [key for key in result.keys() if 'continuous' in key.lower()][0]
            data = result[continuous_key][0].to_pandas()
        except KeyError:
            raise ValueError('No continuous raw data found for the requested query.')
        if not self.disable_info:
            print(self.info_msg + ' Done!', end='\r')
        return DataFrameReader(data, function_name, additional_columns=self.additional_columns,
                               disable_info=True).read()
