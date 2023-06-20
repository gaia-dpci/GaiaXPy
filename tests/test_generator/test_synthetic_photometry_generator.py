import unittest

from gaiaxpy.core.config import load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.generator.photometric_system import PhotometricSystem
from gaiaxpy.generator.synthetic_photometry_generator import _generate_synthetic_photometry
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.single_synthetic_photometry import SingleSyntheticPhotometry
from tests.files.paths import mean_spectrum_avro_file, mean_spectrum_csv_file, mean_spectrum_xml_file,\
    mean_spectrum_xml_plain_file, mean_spectrum_fits_file

continuous_parser = InternalContinuousParser()

# Parse files
parsed_covariance, _ = continuous_parser._parse(mean_spectrum_avro_file)
parsed_correlation_csv, _ = continuous_parser._parse(mean_spectrum_csv_file)
parsed_correlation_fits, _ = continuous_parser._parse(mean_spectrum_fits_file)
parsed_correlation_xml_plain, _ = continuous_parser._parse(mean_spectrum_xml_plain_file)
parsed_correlation_xml, _ = continuous_parser._parse(mean_spectrum_xml_file)

phot_system_johnson = PhotometricSystem.JKC
phot_system_sdss = PhotometricSystem.SDSS
system_johnson_label = phot_system_johnson.get_system_label()
system_sdss_label = phot_system_sdss.get_system_label()
label = 'photsystem'


class TestSyntheticPhotometryGeneratorCSV(unittest.TestCase):

    def test_generate_synthetic_photometry(self):
        xp_sampling = load_xpsampling_from_xml(system=system_johnson_label)
        xp_sampling_grid, xp_merge = load_xpmerge_from_xml(system=system_johnson_label)

        # create sampled basis functions
        sampled_basis_func = {}
        for band in BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_sampling[band])
        photometry_list = []
        for row in parsed_correlation_csv.to_dict('records'):
            synthetic_photometry = _generate_synthetic_photometry(row, sampled_basis_func, xp_merge,
                                                                  phot_system_johnson)
            photometry_list.append(synthetic_photometry)
        first_row = parsed_correlation_csv.iloc[0]
        synthetic_photometry = _generate_synthetic_photometry(first_row, sampled_basis_func, xp_merge,
                                                              phot_system_johnson)
        self.assertIsInstance(synthetic_photometry, SingleSyntheticPhotometry)


class TestSyntheticPhotometryGeneratorFITS(unittest.TestCase):

    def test_generate_synthetic_photometry(self):
        xp_sampling = load_xpsampling_from_xml(system_johnson_label)
        xp_sampling_grid, xp_merge = load_xpmerge_from_xml(system_johnson_label)

        # create sampled basis functions
        sampled_basis_func = {}
        for band in BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_sampling[band])
        photometry_list = []
        for row in parsed_correlation_fits.to_dict('records'):
            synthetic_photometry = _generate_synthetic_photometry(row, sampled_basis_func, xp_merge,
                                                                  phot_system_johnson)
            photometry_list.append(synthetic_photometry)
        first_row = parsed_correlation_fits.iloc[0]
        synthetic_photometry = _generate_synthetic_photometry(
            first_row, sampled_basis_func, xp_merge, phot_system_johnson)
        self.assertIsInstance(synthetic_photometry, SingleSyntheticPhotometry)


class TestSyntheticPhotometryGeneratorXMLPlain(unittest.TestCase):

    def test_generate_synthetic_photometry(self):
        xp_sampling = load_xpsampling_from_xml(system_sdss_label)
        xp_sampling_grid, xp_merge = load_xpmerge_from_xml(system_sdss_label)
        # Create sampled basis functions
        sampled_basis_func = {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_sampling[band]) for
                              band in BANDS}
        photometry_list = []
        for row in parsed_correlation_xml_plain.to_dict('records'):
            synthetic_photometry = _generate_synthetic_photometry(row, sampled_basis_func, xp_merge, phot_system_sdss)
            photometry_list.append(synthetic_photometry)
        first_row = parsed_correlation_xml_plain.iloc[0]
        synthetic_photometry = _generate_synthetic_photometry(first_row, sampled_basis_func, xp_merge, phot_system_sdss)
        self.assertIsInstance(synthetic_photometry, SingleSyntheticPhotometry)


class TestSyntheticPhotometryGeneratorXML(unittest.TestCase):

    def test_generate_synthetic_photometry(self):
        xp_sampling = load_xpsampling_from_xml(system_sdss_label)
        xp_sampling_grid, xp_merge = load_xpmerge_from_xml(system_sdss_label)
        # Create sampled basis functions
        sampled_basis_func = {}
        for band in BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_sampling[band])
        photometry_list = []
        for row in parsed_correlation_xml.to_dict('records'):
            synthetic_photometry = _generate_synthetic_photometry(row, sampled_basis_func, xp_merge, phot_system_sdss)
            photometry_list.append(synthetic_photometry)
        first_row = parsed_correlation_xml.iloc[0]
        synthetic_photometry = _generate_synthetic_photometry(first_row, sampled_basis_func, xp_merge, phot_system_sdss)
        self.assertIsInstance(synthetic_photometry, SingleSyntheticPhotometry)


class TestSyntheticPhotometryGeneratorAVRO(unittest.TestCase):

    def test_generate_synthetic_photometry(self):
        xp_sampling = load_xpsampling_from_xml(system_johnson_label)
        xp_sampling_grid, xp_merge = load_xpmerge_from_xml(system_johnson_label)
        # Create sampled basis functions
        sampled_basis_func = {}
        for band in BANDS:
            sampled_basis_func[band] = SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_sampling[band])
        first_row = parsed_covariance.iloc[0]
        synthetic_photometry = _generate_synthetic_photometry(first_row, sampled_basis_func, xp_merge,
                                                              phot_system_johnson)
        self.assertIsInstance(synthetic_photometry, SingleSyntheticPhotometry)
