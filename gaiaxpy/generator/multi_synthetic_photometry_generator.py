from .synthetic_photometry_generator import SyntheticPhotometryGenerator
from gaiaxpy.core import _load_xpmerge_from_csv, _load_xpsampling_from_csv
from gaiaxpy.spectrum import MultiSyntheticPhotometry


class MultiSyntheticPhotometryGenerator(SyntheticPhotometryGenerator):

    def __init__(self, photometric_system, bp_model, rp_model):
        self.function_label = 'photsystem'
        if not photometric_system:
            raise ValueError('Photometric system list cannot be empty.')
        self.photometric_system = photometric_system
        self.system_label = [phot_system.get_system_label() for phot_system in self.photometric_system]
        self.bp_model = bp_model
        self.rp_model = rp_model

    def _generate(self, parsed_input_data, extension, output_file, output_format, save_file):
        # Recover attributes
        function_label = self.function_label
        photometric_system = self.photometric_system
        system_label = self.system_label
        bp_model = self.bp_model
        rp_model = self.rp_model
        # Generate XP variables
        xp_sampling_list = [_load_xpsampling_from_csv(function_label, slabel, bp_model, rp_model) for slabel in system_label]
        xp_sampling_grid_xp_merge_tuples_list = [_load_xpmerge_from_csv(function_label, slabel,
                                                 bp_model=bp_model, rp_model=rp_model) for slabel in system_label]
        xp_sampling_grid_list = [element[0] for element in xp_sampling_grid_xp_merge_tuples_list]
        xp_merge_list = [element[1] for element in xp_sampling_grid_xp_merge_tuples_list]
        # Get basis functions list
        sampled_basis_func_list = [self._get_sampled_basis_functions(xp_sampling, xp_sampling_grid)
                                   for xp_sampling, xp_sampling_grid in zip(xp_sampling_list, xp_sampling_grid_list)]
        # One list per system
        photometry_list_of_lists = [self._create_photometry_list(parsed_input_data, phot_system, sampled_basis_func,
                                                                 xp_merge)
                                    for phot_system, sampled_basis_func, xp_merge in
                                    zip(photometric_system, sampled_basis_func_list, xp_merge_list)]
        # Now the first list contains the photometries in all systems for the first source_id, and so on.
        rearranged_photometry_list = [sublist for sublist in zip(*photometry_list_of_lists)]  # list of tuples is enough
        multi_photometry_df = MultiSyntheticPhotometry(photometric_system, rearranged_photometry_list)._generate_output_df()
        return multi_photometry_df
