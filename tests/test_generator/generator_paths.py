import pandas as pd

from tests.files.paths import phot_system_specs_path, phot_system_specs_converters

phot_systems_specs = pd.read_csv(phot_system_specs_path, converters=phot_system_specs_converters,
                                 float_precision='high')
