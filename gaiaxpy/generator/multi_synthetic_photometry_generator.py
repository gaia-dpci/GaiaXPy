from tqdm import tqdm

from gaiaxpy.core.generic_variables import pbar_colour, pbar_units, pbar_message
from gaiaxpy.spectrum.multi_synthetic_photometry import MultiSyntheticPhotometry
from .synthetic_photometry_generator import SyntheticPhotometryGenerator


class MultiSyntheticPhotometryGenerator(SyntheticPhotometryGenerator):

    def __init__(self, photometric_system, bp_model, rp_model):
        self.function_label = 'photsystem'
        if not photometric_system:
            raise ValueError('Photometric system list cannot be empty.')
        self.photometric_system = photometric_system
        self.system_label = [phot_system.get_system_label() for phot_system in self.photometric_system]
        self.bp_model = bp_model
        self.rp_model = rp_model

    def generate(self, parsed_input_data, extension, output_file, output_format, save_file):
        __FUNCTION_KEY = 'photometry'
        # Recover attributes
        systems = self.photometric_system
        internal_systems = [system.value for system in systems]
        # Generate XP variables
        xp_sampling_list = [system.load_xpsampling_from_xml() for system in internal_systems]
        xp_sampling_grid_xp_merge_tuples_list = [system.load_xpmerge_from_xml() for system in internal_systems]
        xp_sampling_grid_list = [element[0] for element in xp_sampling_grid_xp_merge_tuples_list]
        xp_merge_list = [element[1] for element in xp_sampling_grid_xp_merge_tuples_list]
        # Get basis functions list
        sampled_basis_func_list = [self._get_sampled_basis_functions(xp_sampling, xp_sampling_grid) for
                                   xp_sampling, xp_sampling_grid in zip(xp_sampling_list, xp_sampling_grid_list)]
        # One list per system
        photometry_list_of_lists = [self._create_photometry_list(parsed_input_data, phot_system,
                                                                 sampled_basis_func, xp_merge)
                                    for phot_system, sampled_basis_func, xp_merge
                                    in zip(systems, sampled_basis_func_list, xp_merge_list)]
        # Now the first list contains the photometries in all systems for the first source_id, and so on.
        rearranged_photometry_list = [sublist for sublist in tqdm(zip(*photometry_list_of_lists),
                                                                  desc=pbar_message[__FUNCTION_KEY],
                                                                  total=len(parsed_input_data),
                                                                  unit=pbar_units[__FUNCTION_KEY], leave=False,
                                                                  colour=pbar_colour)]
        return MultiSyntheticPhotometry(systems, rearranged_photometry_list)._generate_output_df()
