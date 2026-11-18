import pandas as pd
import pytest

from gaiaxpy import convert
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.input_reader.query_reader import QueryReader

# Regular query
query_0 = "select * from gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816', '5853498713190525696')"
# One single-line comment
query_1 = "select * from gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816', '5853498713190525696') -- This query selects all columns from the specified table"
# More than one single-line comment
query_2 = ("-- This query selects all columns from the specified table\nselect *  -- "
           "Selecting all columns\nfrom gaiadr3.gaia_source  "
           "-- From the Gaia DR3 source table\nWHERE source_id IN ('5762406957886626816', '5853498713190525696')  "
           "-- Where the source_id matches the given values")
# One multi-line comment
query_3 = ("/*\n  This query selects all columns from the gaiadr3.gaia_source table\n  where the source_id is in "
           "the specified list of values.\n*/\nselect * from gaiadr3.gaia_source WHERE source_id IN "
           "('5762406957886626816', '5853498713190525696')")
# More than one multi-line comment
query_4 = ("/*\n  This query selects all columns from the gaiadr3.gaia_source table.\n*/\nselect * \n/*\n  "
           "Filtering rows where the source_id matches one of the specified values.\n*/\nfrom gaiadr3.gaia_source \n"
           "WHERE source_id IN ('5762406957886626816', '5853498713190525696')")
# A combination of the previous ones
query_5 = ("-- This query selects all columns\n/*\n  From the gaiadr3.gaia_source table.\n  The query filters rows"
           "based on source_id.\n*/\nselect * \nfrom gaiadr3.gaia_source  -- Gaia DR3 source table\nWHERE \n  "
           "/* Filtering condition */\n  source_id IN ('5762406957886626816', '5853498713190525696')\n"
           "-- End of the query")
# An empty single-line comment
query_6 = "select * from gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816', '5853498713190525696')  -- "
# An empty multi-line comment
query_7 = "select * from gaiadr3.gaia_source WHERE source_id IN ('5762406957886626816', '5853498713190525696')  /* */"

queries = [query_0, query_1, query_2, query_3, query_4, query_5, query_6, query_7]


@pytest.mark.parametrize('query', queries)
def test_no_marker_preserves_query(query):
    assert QueryReader._add_marker(query, '') == query


@pytest.mark.parametrize('query', queries)
def test_add_markers_to_query(query):
    comment = 'This is a test from within GaiaXPy'
    assert QueryReader._add_marker(query, comment) == f'--{comment}\n{query}'


@pytest.mark.parametrize('value', ["'a--b'", "'a/*b*/c'", "'selection'", "'it''s selected'",
                                   '"selection"'])
def test_marker_preserves_quoted_values_and_identifiers(value):
    query = f'SELECT source_id FROM gaiadr3.gaia_source WHERE designation = {value}'
    assert QueryReader._add_marker(query, 'GaiaXPy') == f'--GaiaXPy\n{query}'


def test_marker_preserves_nested_selects_and_existing_comments():
    query = 'SELECT source_id /* select */ FROM (SELECT source_id FROM user_table) -- keep this'
    assert QueryReader._add_marker(query, 'GaiaXPy') == f'--GaiaXPy\n{query}'


def test_marker_keeps_custom_multiline_text_inside_comment():
    query = 'SELECT source_id FROM gaiadr3.gaia_source'
    assert QueryReader._add_marker(query, 'GaiaXPy\r\nextra\ntext') == f'--GaiaXPy extra text\n{query}'


@pytest.mark.archive
def test_launch_query_with_comment():
    comment = 'Launching query with comment from within GaiaXPy'
    result, extension = QueryReader(query_0, convert, truncation=True, release=RELEASES.dr3).read(comment)
    assert isinstance(result, pd.DataFrame)
    assert extension is None
