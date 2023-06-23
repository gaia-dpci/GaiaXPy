import pandas as pd

from tests.files.paths import found_extrema_real_path, found_extrema_trunc_real_path, found_extrema_no_bp_real_path, \
    found_fast_real_path, found_fast_trunc_real_path, found_fast_no_bp_real_path, found_lines_real_path, \
    found_lines_trunc_real_path, found_lines_no_bp_real_path
from tests.utils.utils import get_converters

found_extrema_real = pd.read_csv(found_extrema_real_path)
found_extrema_trunc_real = pd.read_csv(found_extrema_trunc_real_path)
found_extrema_no_bp_real = pd.read_csv(found_extrema_no_bp_real_path)

found_fast_real = pd.read_csv(found_fast_real_path, converters=get_converters(['extrema_bp', 'extrema_rp']))
found_fast_trunc_real = pd.read_csv(found_fast_trunc_real_path, converters=get_converters(['extrema_bp', 'extrema_rp']))
found_fast_no_bp_real = pd.read_csv(found_fast_no_bp_real_path, converters=get_converters(['extrema_bp', 'extrema_rp']))

found_lines_real = pd.read_csv(found_lines_real_path)
found_lines_trunc_real = pd.read_csv(found_lines_trunc_real_path)
found_lines_no_bp_real = pd.read_csv(found_lines_no_bp_real_path)