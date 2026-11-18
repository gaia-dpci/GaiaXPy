""""Avoid pandas >= 3.0 warning due to float_precision argument deprecation."""

import pandas as pd
from packaging.version import Version

CSV_FLOAT_PRECISION_KWARGS = (
    {'float_precision': 'round_trip'}
    if Version(pd.__version__) < Version('3.0')
    else {}
)
