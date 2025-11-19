import re

import pandas as pd
import pytest

from gaiaxpy import convert
from gaiaxpy.input_reader.query_reader import QueryReader

# Regular query
query_0 = "select * from gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816', '5853498713190525696')"
# One single-line comment
query_1 = ("select * from gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816', '5853498713190525696') "
           "-- This query selects all columns from the specified table")
# More than one single-line comment
query_2 = ("-- This query selects all columns from the specified table\nselect *  -- Selecting all "
           "columns\nfrom gaiadr3.gaia_source  -- From the Gaia DR3 source table\nWHERE source_id IN"
           " ('5762406957886626816', '5853498713190525696')  -- Where the source_id matches the given values")
# One multi-line comment
query_3 = ("/*\n  This query selects all columns from the gaiadr3.gaia_source table\n  where the source_id "
           "is in the specified list of values.\n*/\nselect * from gaiadr3.gaia_source WHERE source_id IN "
           "('5762406957886626816', '5853498713190525696')")
# More than one multi-line comment
query_4 = ("/*\n  This query selects all columns from the gaiadr3.gaia_source table.\n*/\nselect * \n/*\n  "
           "Filtering rows where the source_id matches one of the specified values.\n*/\nfrom "
           "gaiadr3.gaia_source \nWHERE source_id IN ('5762406957886626816', '5853498713190525696')")
# A combination of the previous ones
query_5 = ("-- This query selects all columns\n/*\n  From the gaiadr3.gaia_source table.\n  The query "
           "filters rows based on source_id.\n*/\nselect * \nfrom gaiadr3.gaia_source  -- Gaia DR3 source "
           "table\nWHERE \n  /* Filtering condition */\n  source_id IN ('5762406957886626816', "
           "'5853498713190525696')\n-- End of the query")
# An empty single-line comment
query_6 = "select * from gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816', '5853498713190525696')  -- "
# An empty multi-line comment
query_7 = "select * from gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816', '5853498713190525696')  /* */"

queries = [query_0, query_1, query_2, query_3, query_4, query_5, query_6, query_7]


def clean_query(_query):
    # Remove multiple line spaces, line breaks, etc.
    return re.sub(r'\s+', ' ', _query.replace('\n', '').replace('\r', '').strip())


def test_remove_comments_from_query():
    comment = ''
    processed_queries = [clean_query(QueryReader._add_marker(query, comment)) for query in queries]
    assert len(set(processed_queries)) == 1  # All queries are equivalent


def test_add_markers_to_query():
    comment = 'This is a test from within GaiaXPy'
    processed_queries = [clean_query(QueryReader._add_marker(query, comment)) for query in queries]
    assert len(set(processed_queries)) == 1


@pytest.mark.archive
def test_launch_query_with_comment():
    comment = 'Launching query with comment from within GaiaXPy'
    result, extension = QueryReader(query_3, convert, truncation=True).read('Gaia DR3', comment)
    assert isinstance(result, pd.DataFrame)
    assert extension is None
