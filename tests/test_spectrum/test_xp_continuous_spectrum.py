from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.generic_spectrum import Spectrum
from gaiaxpy.spectrum.utils import _correlation_to_covariance_dr3int4
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum
from gaiaxpy.spectrum.xp_spectrum import XpSpectrum
from tests.files.paths import mean_spectrum_csv_file


def test_init():
    parser = InternalContinuousParser()
    correlation_parsed_file, _ = parser.parse_file(mean_spectrum_csv_file)
    # Create single BP and single RP spectrum
    row = correlation_parsed_file.head(1)
    for band in BANDS:
        correlation_matrix = row[f'{band}_coefficient_correlations'][0]
        parameters = row[f'{band}_coefficients'][0]
        standard_deviation = row[f'{band}_standard_deviation'][0]
        covariance_matrix = _correlation_to_covariance_dr3int4(correlation_matrix,
                                                               row[f'{band}_coefficient_errors'][0],
                                                               row[f'{band}_standard_deviation'][0])
        continuous_spectrum = XpContinuousSpectrum(row['source_id'][0], band, parameters, covariance_matrix,
                                                   standard_deviation)
        assert isinstance(continuous_spectrum, XpContinuousSpectrum)
        assert isinstance(continuous_spectrum, XpSpectrum)
        assert isinstance(continuous_spectrum, Spectrum)
