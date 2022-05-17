from astroquery.gaia import GaiaClass
from .dataframe_reader import DataFrameReader
from .archive_reader import ArchiveReader

not_supported_functions = ['apply_colour_equation']


class QueryReader(ArchiveReader):

    def __init__(self, content, function, user=None, password=None):
        self.content = content
        super(QueryReader, self).__init__(function, user, password)

    def _read(self, data_release='Gaia DR3_INT6'):
        query = self.content
        function_name = self.function.__name__
        if function_name in not_supported_functions:
            raise ValueError(f'Function {function_name} does not support receiving a query as input.')
        # Connect to geapre
        gaia = GaiaClass(gaia_tap_server='https://geapre.esac.esa.int/', gaia_data_server='https://geapre.esac.esa.int/')
        self._login(gaia)
        # ADQL query
        job = gaia.launch_job_async(query, dump_to_file=False)
        ids = job.get_results()
        result = gaia.load_data(ids=ids['source_id'], format='csv', data_release=data_release,
                                data_structure='raw', retrieval_type='XP_CONTINUOUS', avoid_datatype_check=True)
        try:
            continuous_key = [key for key in result.keys() if 'continuous' in key.lower()][0]
            data = result[continuous_key][0].to_pandas()
        # TODO: More granular error management required.
        except KeyError:
            raise ValueError('No continuous raw data found for the requested query.')
        return DataFrameReader(data)._read_df()
