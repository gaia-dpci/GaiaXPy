"""Input files containing continuous XP spectra."""
from tests.files.paths import input_files_path

# DR3 continuous mean spectra
dr3_spectra_files = input_files_path / 'dr3_spectra'
dr3_continuous_mean_path = dr3_spectra_files / 'xp_continuous'
dr3_unzipped_files_path = dr3_continuous_mean_path / 'unzipped_files'

dr3_mean_spectra_avro_file = dr3_unzipped_files_path / 'MeanSpectrumSolutionWithCov.avro'
dr3_mean_spectra_csv_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW.csv'
dr3_mean_spectra_ecsv_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW.ecsv'
dr3_mean_spectra_fits_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW.fits'
dr3_mean_spectra_xml_binary_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_binary.xml'
dr3_mean_spectra_xml_plain_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_plain.xml'

dr3_with_missing_bp_csv_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_with_missing_BP.csv'
dr3_with_missing_bp_ecsv_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_with_missing_BP.ecsv'
dr3_with_missing_bp_fits_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_with_missing_BP.fits'
dr3_with_missing_bp_xml_binary_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_with_missing_BP_binary.xml'
dr3_with_missing_bp_xml_plain_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_with_missing_BP_plain.xml'

dr3_missing_bp_csv_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.csv'
dr3_missing_bp_ecsv_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.ecsv'
dr3_missing_bp_fits_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_missing_BP_dr3int6.fits'
dr3_missing_bp_xml_binary_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_missing_BP_dr3int6_binary.xml'
dr3_missing_bp_xml_plain_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_missing_BP_dr3int6_plain.xml'

dr3_colour_eq_csv_file = dr3_unzipped_files_path / 'XP_CONTINUOUS_RAW_colour_eq_dr3int6.csv'

# Gaia Archive ZIP downloads: one raw table or one file per source
dr3_zipped_raw_path = dr3_continuous_mean_path / 'zipped_raw_files'
dr3_zipped_individual_path = dr3_continuous_mean_path / 'zipped_individual_files'

dr3_zipped_raw_files = [
    dr3_zipped_raw_path / 'XP_CONTINUOUS_RAW_with_missing_BP_CSV.zip',
    dr3_zipped_raw_path / 'XP_CONTINUOUS_RAW_with_missing_BP_ECSV.zip',
    dr3_zipped_raw_path / 'XP_CONTINUOUS_RAW_with_missing_BP_FITS.zip',
    dr3_zipped_raw_path / 'XP_CONTINUOUS_RAW_with_missing_BP_XML_plain.zip',
    dr3_zipped_raw_path / 'XP_CONTINUOUS_RAW_with_missing_BP_XML_binary.zip'
]

dr3_zipped_individual_files = [
    dr3_zipped_individual_path / 'XP_CONTINUOUS_RAW_with_missing_BP_CSV.zip',
    dr3_zipped_individual_path / 'XP_CONTINUOUS_RAW_with_missing_BP_ECSV.zip',
    dr3_zipped_individual_path / 'XP_CONTINUOUS_RAW_with_missing_BP_FITS.zip',
    dr3_zipped_individual_path / 'XP_CONTINUOUS_RAW_with_missing_BP_XML_plain.zip',
    dr3_zipped_individual_path / 'XP_CONTINUOUS_RAW_with_missing_BP_XML_binary.zip'
]
