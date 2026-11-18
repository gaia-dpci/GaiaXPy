from collections import namedtuple
from dataclasses import dataclass

from gaiaxpy.core.satellite import BANDS

pbar_colour = '#509faf'
pbar_message = {'calibrator': 'Calibrating data',
                'colour_eq': 'Applying colour equation',
                'converter': 'Converting data',
                'correction': 'Correcting systems',
                'design': 'Evaluating design matrices',
                'photometry': 'Generating photometry'}
pbar_units = {'calibrator': 'spec',
              'colour_eq': 'syst',
              'converter': 'spec',
              'correction': 'syst',
              'design': 'band',
              'photometry': 'spec'}

# Data releases
InvBasisTypes = namedtuple('Releases', 'dr3')
RELEASES = InvBasisTypes('dr3')

release_solution_id = {RELEASES.dr3: ['4545469030156206080', '4545469030156206081']}

n_params_dict = {RELEASES.dr3: {BANDS.bp: 55, BANDS.rp: 55}}

# Generator
ADDITIONAL_SYSTEM_PREFIX = 'USER'

# BP/RP models
# Define allowed and default models per release
ALLOWED_MODELS = {
    RELEASES.dr3: {BANDS.bp: ['v375wi'], BANDS.rp: ['v142r']},
}

DEFAULT_MODELS = {
    RELEASES.dr3: {BANDS.bp: 'v375wi', BANDS.rp: 'v142r'},
}

InvBasisTypes = namedtuple('CalibratorBasisTypes', 'basic')
INV_BASIS_TYPES = InvBasisTypes('basic')

YAML_EXTENSIONS = ('.yaml', '.yml')

# Functions for which the data release should not be inferred from the input data.
# Their release is determined by other function-specific inputs or configuration.
RELEASE_REDUNDANT_FUNCTIONS = ('apply_error_correction',)


@dataclass(frozen=True)
class ModelPair:
    bp_model: str
    rp_model: str


VALID_EXTENSIONS = ['avro', 'csv', 'ecsv', 'fits', 'xml']
