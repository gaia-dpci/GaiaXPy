import unittest

from gaiaxpy.core.config import load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.generator.photometric_system import PhotometricSystem
from gaiaxpy.generator.synthetic_photometry_generator import _generate_synthetic_photometry
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.single_synthetic_photometry import SingleSyntheticPhotometry
from tests.files.paths import mean_spectrum_avro_file, mean_spectrum_csv_file, mean_spectrum_xml_file, \
    mean_spectrum_xml_plain_file, mean_spectrum_fits_file, mean_spectrum_ecsv_file

continuous_parser = InternalContinuousParser()

# Parse files
parsed_covariance, _ = continuous_parser._parse(mean_spectrum_avro_file)
parsed_correlation_csv, _ = continuous_parser._parse(mean_spectrum_csv_file)
parsed_correlation_ecsv, _ = continuous_parser._parse(mean_spectrum_ecsv_file)
parsed_correlation_fits, _ = continuous_parser._parse(mean_spectrum_fits_file)
parsed_correlation_xml_plain, _ = continuous_parser._parse(mean_spectrum_xml_plain_file)
parsed_correlation_xml, _ = continuous_parser._parse(mean_spectrum_xml_file)

phot_system_johnson = PhotometricSystem.JKC
phot_system_sdss = PhotometricSystem.SDSS
system_johnson_label = phot_system_johnson.get_system_label()
system_sdss_label = phot_system_sdss.get_system_label()

input_data = [parsed_correlation_csv, parsed_correlation_fits, parsed_correlation_xml_plain, parsed_correlation_xml,
              parsed_covariance, parsed_correlation_ecsv]
system_label = [system_johnson_label, system_johnson_label, system_sdss_label, system_sdss_label, system_johnson_label,
                system_johnson_label]
phot_systems = [phot_system_johnson, phot_system_johnson, phot_system_sdss, phot_system_sdss, phot_system_johnson,
                phot_system_johnson]


class TestSyntheticPhotometryGenerator(unittest.TestCase):

    def test_generate_synthetic_photometry(self):
        for df, label, phot_sys in zip(input_data, system_label, phot_systems):
            xp_sampling = load_xpsampling_from_xml(system=label)
            xp_sampling_grid, xp_merge = load_xpmerge_from_xml(system=label)
            # Create sampled basis functions
            sampled_basis_func = {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_sampling[band])
                                  for band in BANDS}
            synthetic_photometry = _generate_synthetic_photometry(df.iloc[0], sampled_basis_func, xp_merge,
                                                                  phot_system_johnson)
            self.assertIsInstance(synthetic_photometry, SingleSyntheticPhotometry)
