from gaiaxpy.core.config import load_xpmerge_from_file, load_xpsampling_from_file
from gaiaxpy.core.config_dispatcher import GeneratorDispatcher
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.generator.synthetic_photometry_generator import _generate_synthetic_photometry
from gaiaxpy.input_reader.required_columns import MANDATORY_INPUT_COLS, CORR_INPUT_COLUMNS, COV_INPUT_COLUMNS
from gaiaxpy.photometric_system.photometric_system import PhotometricSystem
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.single_synthetic_photometry import SingleSyntheticPhotometry
from tests.files.continuous import (dr3_mean_spectra_avro_file, dr3_mean_spectra_csv_file,
                                    dr3_mean_spectra_xml_binary_file, dr3_mean_spectra_xml_plain_file,
                                    dr3_mean_spectra_fits_file, dr3_mean_spectra_ecsv_file)


def test_generate_synthetic_photometry():
    corr_continuous_parser = InternalContinuousParser(MANDATORY_INPUT_COLS['generate'] + CORR_INPUT_COLUMNS)
    cov_continuous_parser = InternalContinuousParser(MANDATORY_INPUT_COLS['generate'] + COV_INPUT_COLUMNS)
    # Parse files
    parsed_covariance, _ = cov_continuous_parser.parse_file(dr3_mean_spectra_avro_file)
    parsed_correlation_csv, _ = corr_continuous_parser.parse_file(dr3_mean_spectra_csv_file)
    parsed_correlation_ecsv, _ = corr_continuous_parser.parse_file(dr3_mean_spectra_ecsv_file)
    parsed_correlation_fits, _ = corr_continuous_parser.parse_file(dr3_mean_spectra_fits_file)
    parsed_correlation_xml_plain, _ = corr_continuous_parser.parse_file(dr3_mean_spectra_xml_plain_file)
    parsed_correlation_xml, _ = corr_continuous_parser.parse_file(dr3_mean_spectra_xml_binary_file)

    phot_system_johnson = PhotometricSystem.DR3_JKC
    phot_system_sdss = PhotometricSystem.DR3_SDSS
    system_johnson_label = phot_system_johnson.get_system_label()
    system_sdss_label = phot_system_sdss.get_system_label()

    input_data = [parsed_correlation_csv, parsed_correlation_fits, parsed_correlation_xml_plain, parsed_correlation_xml,
                  parsed_covariance, parsed_correlation_ecsv]
    system_label = [system_johnson_label, system_johnson_label, system_sdss_label, system_sdss_label,
                    system_johnson_label,
                    system_johnson_label]
    phot_systems = [phot_system_johnson, phot_system_johnson, phot_system_sdss, phot_system_sdss, phot_system_johnson,
                    phot_system_johnson]
    for df, label, phot_sys in zip(input_data, system_label, phot_systems):
        config_file = GeneratorDispatcher().build(systems=[phot_sys], bp_model='v375wi', rp_model='v142r',
                                                  parsed_input_data=df, release=RELEASES.dr3)
        xp_sampling = load_xpsampling_from_file(config_file)
        xp_sampling_grid, xp_merge = load_xpmerge_from_file(config_file)
        # Create sampled basis functions
        sampled_basis_func = {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_sampling[band])
                              for band in BANDS}
        synthetic_photometry = _generate_synthetic_photometry(df.iloc[0], sampled_basis_func, xp_merge,
                                                              False, phot_system_johnson)
        assert isinstance(synthetic_photometry, SingleSyntheticPhotometry)
