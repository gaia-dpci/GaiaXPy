from os.path import join

import pandas as pd

from tests.files.paths import files_path, phot_system_specs_path, phot_system_specs_converters

phot_systems_specs = pd.read_csv(phot_system_specs_path, converters=phot_system_specs_converters,
                                 float_precision='round_trip')

additional_filters_dir = join(files_path, 'additional_filters')
additional_filters_dup_dir = join(files_path, 'additional_filters_duplicate')
