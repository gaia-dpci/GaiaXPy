from os import listdir
from os.path import join, isfile
from typing import Optional, Tuple

import numpy as np
from yaml import safe_load

from gaiaxpy.config.paths import config_path
from gaiaxpy.core.generic_functions import format_list_to_str_msg
from gaiaxpy.core.generic_variables import RELEASES, ALLOWED_MODELS, DEFAULT_MODELS, ModelPair, INV_BASIS_TYPES
from gaiaxpy.core.release_resolution import get_release_from_data
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.photometric_system.utils import _get_system_label


def get_models_for_version(release: str, bp_model: Optional[str] = None, rp_model: Optional[str] = None) -> ModelPair:
    if bp_model is None:
        bp_model = DEFAULT_MODELS[release][BANDS.bp]
    if rp_model is None:
        rp_model = DEFAULT_MODELS[release][BANDS.rp]

    bp_allowed = ALLOWED_MODELS[release][BANDS.bp]
    rp_allowed = ALLOWED_MODELS[release][BANDS.rp]

    if bp_model not in bp_allowed:
        raise ValueError(f"For release {release}, bp_model must be one of {format_list_to_str_msg(bp_allowed)}, "
                         f"but is '{bp_model}'")
    if rp_model not in rp_allowed:
        raise ValueError(f"For release {release}, rp_model must be one of {format_list_to_str_msg(rp_allowed)}, "
                         f"but is '{rp_model}'")

    return ModelPair(bp_model, rp_model)


class Config:
    def __init__(self):
        self._load()

    def _load(self):
        with open(join(config_path, 'config.yaml'), 'r') as file:
            self.config_dict = safe_load(file)

    def get(self):
        return self.config_dict


class ConfigDispatcher:
    def __init__(self):
        self.config = None
        self.function = None

    @staticmethod
    def verify_resolve_args(parsed_input_data: 'pd.DataFrame' = None, release: str = None):
        from pandas import DataFrame as pdDf
        if parsed_input_data is not None and not isinstance(parsed_input_data, pdDf):
            raise TypeError("'parsed_input_data' must be of type 'pandas.DataFrame'.")
        if release is not None and not isinstance(release, str):
            raise TypeError("'release' must be of type 'str'.")

    def verify_data_release(self, parsed_input_data, release='dr3'):
        if parsed_input_data is not None:
            computed_release = get_release_from_data(parsed_input_data, self.function)
            if computed_release is not None and computed_release != RELEASES.dr3:
                raise ValueError("The input data appears to belong to a data release "
                                 "not supported by this version of GaiaXPy. "
                                 "Only Gaia DR3 data is supported.")

        return RELEASES.dr3


class CalibratorDispatcher(ConfigDispatcher):
    def __init__(self):
        super().__init__()
        self.config = Config().get()['calibrator']
        self.function = 'calibrate'

    def resolve(self, parsed_input_data: 'pd.DataFrame' = None, release: str = None,
                sampling: Optional[np.ndarray] = None, basis_type: str = None) -> Tuple[dict, str]:
        ConfigDispatcher().verify_resolve_args(parsed_input_data=parsed_input_data, release=release)
        release = self.verify_data_release(parsed_input_data, release)
        filenames_dict = self.config[release]
        filenames_dict['sampling']['path'] = filenames_dict['sampling']['path'] + f'/{basis_type}'
        sampling_key = 'sampling' if sampling is not None else 'nosampling'
        return filenames_dict[sampling_key], release

    @staticmethod
    def verify_basis(basis_type: str | None, sampling: np.ndarray | None, release: str):
        if basis_type is None:
            raise ValueError('A basis type is required')
        if not isinstance(basis_type, str):
            raise TypeError(f"The variable 'basis_type' should be a string but is {type(basis_type).__name__}")
        basis_type = basis_type.lower()
        if basis_type not in INV_BASIS_TYPES:
            raise ValueError(f"Basis type is {basis_type}, which is not allowed. Available types are: "
                             f"{format_list_to_str_msg(INV_BASIS_TYPES)}.")
        if release == RELEASES.dr3 and basis_type != INV_BASIS_TYPES.basic:
            raise ValueError(
                f"The data release to use is DR3 but the type of inverse basis selected is '{basis_type}'. "
                "Only the 'basic' type can be used with DR3 data.")
        if sampling is None and basis_type != INV_BASIS_TYPES.basic:
            raise ValueError('Non-basic inverse basis functions can only be using when providing a sampling')
        return basis_type

    def build(self, sampling, **kwargs):
        allowed_keys = {'bp_model', 'rp_model', 'systems', 'parsed_input_data', 'release', 'basis_type'}
        for key in kwargs:
            if key not in allowed_keys:
                raise TypeError(f"Unexpected keyword argument '{key}'")
        parsed_input_data = kwargs.get('parsed_input_data')
        bp_model = kwargs.get('bp_model')
        rp_model = kwargs.get('rp_model')
        release = kwargs.get('release')
        basis_type = kwargs.get('basis_type')
        basis_type = self.verify_basis(basis_type, sampling, release)
        ConfigDispatcher().verify_resolve_args(parsed_input_data=parsed_input_data, release=release)
        config_dict, computed_release = self.resolve(parsed_input_data=parsed_input_data, release=release,
                                                     sampling=sampling, basis_type=basis_type)
        if release is not None and computed_release != release:
            raise ValueError('Release changed! This should not happen.')
        if sampling is None:
            return self.build_nosampling(config_dict, release=computed_release, bp_model=bp_model, rp_model=rp_model)
        else:
            return self.build_sampling(config_dict, release=computed_release, bp_model=bp_model, rp_model=rp_model,
                                       sampling=sampling, basis_type=basis_type)

    @staticmethod
    def build_nosampling(config_dict, **kwargs):
        bp_model = kwargs.get('bp_model')
        rp_model = kwargs.get('rp_model')
        release = kwargs['release']
        model_pair = get_models_for_version(release, bp_model=bp_model, rp_model=rp_model)
        return config_path / config_dict['path'] / config_dict['generic'].replace(
            '{model}', f'{model_pair.bp_model}_{model_pair.rp_model}')

    @staticmethod
    def build_sampling(config_dict, **kwargs):
        sampling = kwargs['sampling']
        if sampling is None:
            raise ValueError('Sampling cannot be None when building name of file with sampling.')
        bp_model = kwargs['bp_model']
        rp_model = kwargs['rp_model']
        release = kwargs['release']
        if release is None:
            raise ValueError('Release cannot be None when building name of file with sampling.')
        model_pair = get_models_for_version(release, bp_model=bp_model, rp_model=rp_model)
        basis_type = kwargs['basis_type']
        kinds = ['dispersion', 'response', 'bases']
        files_dict = {}
        for band, model in zip(BANDS, [model_pair.bp_model, model_pair.rp_model]):
            files_dict[band] = {}
            for kind in kinds:
                filename = config_dict['generic'].replace('{xp}', band).replace('{model}', model).replace('{kind}',
                                                                                                          kind)
                __file = config_path / config_dict['path'] / filename
                if not isfile(__file):
                    raise FileNotFoundError(f'File {__file} does not exist.')
                files_dict[band][kind] = __file
        if 'bases_file' in config_dict.keys():
            __bases_file = config_path / config_dict['bases_file']
            if not isfile(__bases_file):
                raise FileNotFoundError(f'File {__bases_file} does not exist.')
            files_dict['bases_file'] = __bases_file
        return files_dict


class ConverterDispatcher(ConfigDispatcher):
    def __init__(self):
        super().__init__()
        self.config = Config().get()['converter']
        self.function = 'convert'

    def resolve(self, parsed_input_data: 'pd.DataFrame' = None, release: str = None):
        ConfigDispatcher().verify_resolve_args(parsed_input_data=parsed_input_data, release=release)
        release = self.verify_data_release(parsed_input_data, release)
        return self.config[release]

    def build(self, **kwargs):
        parsed_input_data = kwargs.get('parsed_input_data')
        release = kwargs.get('release')
        release_dict = self.resolve(parsed_input_data=parsed_input_data, release=release)
        return config_path / release_dict['path'] / release_dict['file']


class GeneratorDispatcher(ConfigDispatcher):
    def __init__(self):
        super().__init__()
        self.config = Config().get()['generator']
        self.function = 'generate'

    def resolve(self, photsystem: bool, parsed_input_data: 'pd.DataFrame' = None, release: str = None,
                systems: Optional[list] = None):
        ConfigDispatcher().verify_resolve_args(parsed_input_data=parsed_input_data, release=release)
        if photsystem and not systems:
            raise ValueError('Photsystem cannot be None when building name of file with photsystem.')
        release = self.verify_data_release(parsed_input_data, release)
        release_dict = self.config[release]
        if photsystem:
            cd = release_dict['photsystem']
        else:
            cd = release_dict['xpfilter']
        return release, cd

    def build(self, **kwargs):
        allowed_keys = {'bp_model', 'rp_model', 'systems', 'parsed_input_data', 'release'}
        for key in kwargs:
            if key not in allowed_keys:
                raise TypeError(f"Unexpected keyword argument '{key}'")
        parsed_input_data = kwargs.get('parsed_input_data')
        bp_model = kwargs['bp_model']
        rp_model = kwargs['rp_model']
        release = kwargs.get('release')
        systems = kwargs.get('systems')
        computed_release, config_dict = self.resolve(parsed_input_data=parsed_input_data, release=release,
                                                     photsystem=systems is not None, systems=systems)
        if systems:
            if not isinstance(systems, list):
                raise TypeError("'system' must be of type 'list'.")
            else:
                if computed_release == RELEASES.dr3:
                    return self.build_photsystem_dr3(config_dict=config_dict, systems=systems, bp_model=bp_model,
                                                     rp_model=rp_model)
                else:
                    raise ValueError(f'Release {computed_release} not implemented.')
        else:
            return self.build_xpfilter(config_dict=config_dict, bp_model=bp_model, rp_model=rp_model)

    @staticmethod
    def build_photsystem_dr3(config_dict, systems, bp_model, rp_model):
        label = [_get_system_label(system) if isinstance(system, str) else system.get_system_label() for system
                 in systems][0]
        file = config_path / config_dict['path'] / config_dict['filter'].replace('{system}', label).replace(
            '{model}', f'{bp_model}_{rp_model}')
        if isfile(file):
            return file
        else:
            raise ValueError(f'File {file} for system {label} not found.')

    @staticmethod
    def build_xpfilter(config_dict, bp_model, rp_model):
        file = config_path / config_dict['path'] / config_dict['generic'].replace('{model}', f'{bp_model}_{rp_model}')
        if isfile(file):
            return file
        else:
            raise ValueError(f'File {file} not found.')


class ErrorCorrectorDispatcher(ConfigDispatcher):

    def __init__(self):
        super().__init__()
        self.config = Config().get()['error_corrector']

    def resolve(self, release):
        config_dict = self.config[release]
        return config_path / config_dict['path'], config_dict['generic']

    def build_systems_names(self, release):
        correction_path, _ = self.resolve(release)
        correction_files = listdir(correction_path)
        return [filename.split('-')[2] for filename in correction_files]

    def build_system(self, release, system):
        correction_path, generic_system_file = self.resolve(release)
        return config_path / correction_path / generic_system_file.replace('{system}', system)


# Load once
__cal_config_dict = CalibratorDispatcher()
__gen_config_dict = GeneratorDispatcher()
# Public access point
get_cal_dispatcher = lambda: __cal_config_dict
get_gen_dispatcher = lambda: __gen_config_dict
