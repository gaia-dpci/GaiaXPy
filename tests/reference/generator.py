"""Parsed reference data shared by generator tests."""
import pandas as pd

from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from tests.files.generator import phot_system_specs_converters, phot_system_specs_path

phot_systems_specs = pd.read_csv(phot_system_specs_path, converters=phot_system_specs_converters,
                                 **CSV_FLOAT_PRECISION_KWARGS)
