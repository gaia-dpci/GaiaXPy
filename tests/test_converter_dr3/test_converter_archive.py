import numpy.testing as npt
import pytest

from gaiaxpy import convert
from gaiaxpy.core.generic_variables import RELEASES
from tests.reference.converter import missing_solution_df, with_missing_solution_df, with_missing_solution_sampling
from tests.utils.utils import assert_dfs_equal, dr3_missing_bp_source_id


@pytest.mark.archive
@pytest.mark.parametrize('_input,solution', [
    ([dr3_missing_bp_source_id], missing_solution_df),
    (['5853498713190525696', str(dr3_missing_bp_source_id), '5762406957886626816'], with_missing_solution_df),
    (f'SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ({dr3_missing_bp_source_id})', missing_solution_df),
    (f"SELECT * FROM gaiadr3.gaia_source WHERE source_id IN ('5853498713190525696', {str(dr3_missing_bp_source_id)},"
     "'5762406957886626816')", with_missing_solution_df)])
def test_missing_bp(_input, solution):
    output_df, sampling = convert(_input, save_file=False, release=RELEASES.dr3)
    sort_columns = ['source_id', 'xp']
    sorted_output_df = output_df.sort_values(by=sort_columns, ignore_index=True)
    sorted_solution_df = solution.sort_values(by=sort_columns, ignore_index=True)
    assert_dfs_equal(sorted_output_df, sorted_solution_df, rtol=1e-7, atol=1e-7)
    npt.assert_array_equal(sampling, with_missing_solution_sampling)
